import logging

from psycopg2.extensions import AsIs

import skygear
from skygear.utils import db
from skygear.utils.context import current_user_id

from .exc import (NotInConversationException, NotSupportedException,
                  SkygearChatException)
from .message import Message
from .receipt import Receipt
from .user_conversation import UserConversation
from .utils import (_get_schema_name, current_context_has_master_key,
                    is_str_list)

logger = logging.getLogger(__name__)
try:
    # Available in py-skygear v1.6
    from skygear.utils.logging import setLoggerTag
    setLoggerTag(logger, 'chat_plugin')
except ImportError:
    pass


def handle_mark_as_delivered(message_ids: [str]):
    """
    Marking a message as delivered, which should update a receipt for the
    message.
    """
    logger.debug(
        'handle_mark_as_delivered: message_ids: %s',
        ','.join(message_ids)
    )
    mark_messages(message_ids, True, False)


def handle_mark_as_read(message_ids: [str]):
    """
    Marking a message as read, which should update a receipt for the message.

    Since a message that is read is also delivered, both the delivered
    and read date will be updated if such value does not exist.
    """
    logger.debug(
        'handle_mark_as_read: message_ids: %s',
        ','.join(message_ids)
    )
    mark_messages(message_ids, True, True)


def handle_mark_as_read_by_range(from_message_id, to_message_id):
    from_seq = -1
    to_seq = -1
    message_ids = [to_message_id]
    if from_message_id is not None:
        message_ids = [from_message_id] + message_ids

    messages = Message.fetch_all(message_ids)
    conversation_id = None
    for message in messages:
        if message.id.key == from_message_id:
            from_seq = message['seq']
        if message.id.key == to_message_id:
            to_seq = message['seq']
            conversation_id = message.conversation_id

    if conversation_id is None:
        raise SkygearChatException('Unknown conversation')

    messages_to_be_marked = Message.\
        fetch_all_by_conversation_id_and_seq(
                            conversation_id, from_seq, to_seq)
    mark_messages(messages_to_be_marked, True, True)


def __validate_current_user_in_messages(messages, user_id):
    for message in messages:
        if UserConversation.fetch_one(message.conversation_id,
                                      user_id=user_id) is None:
            raise NotInConversationException()


def mark_messages(message_ids, mark_delivered, mark_read):
    """
    Check the receipt before saving.
    TODO: update this checking after role based ACL
    """
    user_id = current_user_id()
    messages = Message.fetch_all(message_ids)
    __validate_current_user_in_messages(messages, user_id)

    new_message_ids = []

    receipts = [Receipt.new(current_user_id(), message_id)
                for message_id in message_ids]
    Receipt.save_all(receipts)

    if mark_delivered:
        new_message_ids += mark_messages_as_delivered(message_ids)

    if mark_read:
        new_message_ids += mark_messages_as_read(message_ids)

    new_message_ids = list(set(new_message_ids))

    __update_and_notify_messages(new_message_ids)


def mark_messages_as_delivered(message_ids):
    undelivered_messages = []
    schema_name = AsIs(_get_schema_name())
    user_id = current_user_id()
    with db.conn() as conn:
        for message_id in message_ids:
            cur = conn.execute('''
                WITH undelivered_receipt AS (
                    SELECT r._id AS _id, r.message AS message_id
                    FROM %(schema_name)s.receipt r
                    WHERE r.message = %(message_id)s
                    AND r.user = %(user_id)s
                    AND delivered_at IS NULL LIMIT 1
                ),
                update_delivered_at AS (
                    UPDATE %(schema_name)s.receipt
                    SET delivered_at = NOW()
                    FROM undelivered_receipt
                    WHERE receipt._id = undelivered_receipt._id
                )
                SELECT message_id
                FROM undelivered_receipt
                ''', {
                    'schema_name': schema_name,
                    'user_id': user_id,
                    'message_id': message_id
            })
            row = cur.fetchone()
            if row is not None:
                undelivered_messages.append(row[0])
    return undelivered_messages


def mark_messages_as_read(message_ids):
    schema_name = AsIs(_get_schema_name())
    user_id = current_user_id()
    unread_message_ids = []

    with db.conn() as conn:
        for message_id in message_ids:
            cur = conn.execute('''
                WITH unread_receipt AS (
                    SELECT r._id AS _id, r.message AS message_id
                    FROM %(schema_name)s.receipt r
                    WHERE r.message = %(message_id)s
                    AND r.user = %(user_id)s
                    AND read_at IS NULL LIMIT 1
                ),
                this_message AS (
                    SELECT message.conversation, message.seq, message._id
                    FROM %(schema_name)s.message, unread_receipt
                    WHERE message._id = unread_receipt.message_id
                    LIMIT 1
                ),
                last_read_message AS(
                    SELECT last_read_message AS _id
                    FROM %(schema_name)s.user_conversation uc,
                         this_message
                    WHERE uc.user = %(user_id)s
                    AND uc.conversation = this_message.conversation
                    LIMIT 1
                )
                ,last_read_message_seq AS (
                    SELECT message.seq
                    FROM %(schema_name)s.message,
                         last_read_message
                    WHERE message._id = last_read_message._id
                    LIMIT 1
                ),
                update_last_read_message AS (
                    UPDATE %(schema_name)s.user_conversation uc
                    SET last_read_message =
                    CASE WHEN
                        this_message.seq > last_read_message_seq.seq
                    THEN
                        this_message._id
                    ELSE
                        last_read_message._id
                    END
                    FROM this_message,
                         last_read_message_seq,
                         last_read_message
                    WHERE uc.user = %(user_id)s
                    AND uc.conversation = this_message.conversation
                ),
                update_read_at AS (
                    UPDATE %(schema_name)s.receipt
                    SET read_at = NOW()
                    FROM unread_receipt
                    WHERE receipt._id = unread_receipt._id
                ),
                update_unread_count AS (
                    UPDATE %(schema_name)s.user_conversation uc
                    SET unread_count =
                    CASE WHEN
                        unread_count <= 0
                    THEN
                        0
                    ELSE
                        unread_count - 1
                    END
                    FROM unread_receipt,
                         this_message
                    WHERE uc.user = %(user_id)s
                    AND uc.conversation = this_message.conversation
                )
                SELECT message_id
                FROM unread_receipt
            ''', {
                'schema_name': schema_name,
                'user_id': user_id,
                'message_id': message_id
            })
            row = cur.fetchone()
            if row is not None:
                unread_message_ids.append(row[0])

    return unread_message_ids


def __update_and_notify_messages(message_ids):
    messages = Message.fetch_all(message_ids)
    with db.conn() as conn:
        for message in messages:
            message.updateMessageStatus(conn)
            message.notifyParticipants()


def handle_get_receipt(message_id):
    """
    Retrieve receipts for a message.
    """
    logging.info("handle_get_receipt: for message_id %s", message_id)
    message = Message.fetch_one(message_id)
    if message is None:
        raise SkygearChatException('Message not found')
    if UserConversation.fetch_one(message.conversation_id) is None:
        raise NotInConversationException()

    return {'receipts': message.getReceiptList()}


def register_receipt_hooks(settings):
    @skygear.before_save("receipt", async=False)
    def receipt_before_save_handler(record, original_record, conn):
        if not current_context_has_master_key():
            raise NotSupportedException()


def register_receipt_lambdas(settings):
    @skygear.op(
        "chat:mark_as_delivered",
        auth_required=True,
        user_required=True
    )
    def mark_as_delivered_lambda(arg):
        if isinstance(arg, list) and is_str_list(arg):
            return handle_mark_as_delivered(arg)
        if isinstance(arg, str):
            return handle_mark_as_delivered([arg])
        raise SkygearChatException('bad request')

    @skygear.op("chat:mark_as_read", auth_required=True, user_required=True)
    def mark_as_read_lambda(arg):
        if isinstance(arg, list) and is_str_list(arg):
            return handle_mark_as_read(arg)
        if isinstance(arg, str):
            return handle_mark_as_read([arg])
        raise SkygearChatException('bad request')

    @skygear.op("chat:get_receipt", auth_required=True, user_required=True)
    def get_receipt_lambda(message_id):
        return handle_get_receipt(message_id)

    @skygear.op("chat:mark_as_read_by_range",
                auth_required=True,
                user_required=True)
    def mark_as_read_by_range_lambda(from_message_id, to_message_id):
        return handle_mark_as_read_by_range(from_message_id, to_message_id)
