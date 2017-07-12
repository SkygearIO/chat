import logging
from collections import Counter

from psycopg2.extensions import AsIs

import skygear
from skygear.container import SkygearContainer
from skygear.options import options as skyoptions
from skygear.transmitter.encoding import deserialize_record
from skygear.utils import db
from skygear.utils.context import current_user_id

from .conversation import Conversation
from .database import Database
from .exc import (NotInConversationException, NotSupportedException,
                  SkygearChatException)
from .message import Message
from .predicate import Predicate
from .query import Query
from .receipt import Receipt, ReceiptCollection
from .utils import (_get_schema_name, current_context_has_master_key,
                    is_str_list)


def handle_mark_as_delivered(message_ids: [str]):
    """
    Marking a message as delivered, which should update a receipt for the
    message.
    """
    logging.debug(
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
    logging.debug(
        'handle_mark_as_read: message_ids: %s',
        ','.join(message_ids)
    )
    mark_messages(message_ids, True, True)


def handle_mark_as_read_by_range(arg):
    from_message_id = None
    to_message_id = None
    to_message_id = arg[-1]
    from_message_id = arg[0]

    from_seq = -1
    to_seq = -1
    message_ids = [to_message_id]
    if from_message_id is not None:
        message_ids = [from_message_id] + message_ids

    messages = Message.fetch(message_ids)
    conversation_id = None
    for message in messages:
        if message.record.id.key == from_message_id:
            from_seq = message.record['seq']
        if message.record.id.key == to_message_id:
            to_seq = message.record['seq']
            conversation_id = Conversation(message
                                           .conversationRecord).record.id.key

    if conversation_id is None:
        raise SkygearChatException('Unknown conversation')

    container = SkygearContainer(api_key=skyoptions.masterkey,
                                 user_id=current_user_id())
    database = Database(container, '_private')
    predicate = Predicate(seq__lte=to_seq,
                          conversation__eq=conversation_id,
                          deleted__eq=False)
    if from_seq >= 0:
        predicate = predicate & Predicate(seq__gte=from_seq)

    query = Query('message', predicate=predicate, limit=None)
    results = [deserialize_record(r).id.key
               for r in database.query(query)["result"]]
    mark_messages(results, True, True)


def __validate_current_user_in_messages(messages, user_id):
    for message in messages:
        conversation = Conversation(message.conversationRecord)
        if not conversation.is_participant(user_id):
            print("user %s is not a participant in conversation %s" %
                  (user_id, conversation.record.id.key))
            raise NotInConversationException()


def __update_and_notify_unread_messages(messages, conn):
    for message in messages:
        message.updateMessageStatus(conn)
        message.notifyParticipants()


def __fetch_receipts(messages, user_id):
    receipt_ids = [Receipt.consistent_id(user_id,
                   message.record.id.key)
                   for message in messages]

    found_receipts = {x.record.id.key: x for x in Receipt.fetch(receipt_ids)}
    return found_receipts


def __update_user_conversations(unread_counter, last_read_messages, conn):
    """
    Update user conversation table based on un-read counts and
    last read messages
    """
    user_id = current_user_id()
    schema_name = AsIs(_get_schema_name())
    for key in unread_counter:
        delta = unread_counter[key]
        if delta == 0:
            continue
        conn.execute('''
            UPDATE %(schema_name)s.user_conversation
            SET
                "unread_count" = "unread_count" - %(delta)s,
                "_updated_at" = CURRENT_TIMESTAMP
            WHERE
                "conversation" = %(conversation_id)s
                AND "user" != %(user_id)s
        ''', {
            'schema_name': schema_name,
            'conversation_id': key,
            'user_id': user_id,
            'delta': delta
        })
        print("updating unread count for user=%s,conversation=%s,delta=%d"
              % (user_id, key, delta))

    for key in last_read_messages:
        m = last_read_messages[key]
        conn.execute('''
            WITH last_read_message_id AS(
                SELECT last_read_message AS id FROM
                %(schema_name)s.user_conversation uc
                WHERE uc.user = %(user_id)s
                AND uc.conversation = %(conversation_id)s),
            message_seq AS (
                SELECT seq FROM %(schema_name)s.message
                WHERE _id IN (SELECT id FROM last_read_message_id)
            )
            UPDATE %(schema_name)s.user_conversation uc SET
                last_read_message = CASE WHEN
                    %(seq)s < (SELECT seq FROM message_seq LIMIT 1)
                THEN
                    last_read_message
                ELSE
                    %(new_id)s
                END
            WHERE uc.user = %(user_id)s
            AND uc.conversation = %(conversation_id)s
        ''', {
            'schema_name': schema_name,
            'conversation_id': key,
            'user_id': user_id,
            'seq': m.record['seq'],
            'new_id': m.record.id.key
        })
        print("updating last_read_message in user=%s,conversation=%s"
              % (user_id, key))


def __update_last_read_messages(last_read_messages, message, key):
    last_read_message = last_read_messages.get(key, None)
    if last_read_message is None:
        last_read_message = message
    if message.record['seq'] > last_read_message.record['seq']:
        last_read_message = message
    last_read_messages[key] = last_read_message


def __get_messages_receipts(messages, user_id):
    output = []
    found_receipts = __fetch_receipts(messages, user_id)
    for message in messages:
        message_id = message.record.id.key
        receipt_id = Receipt.consistent_id(user_id, message_id)
        receipt = found_receipts.get(receipt_id, None)
        if receipt is None:
            receipt = receipt(user_id, message_id)
        output.append((message, receipt))
    return output


def __process_message_receipts(tuples, mark_delivered, mark_read):
    new_receipts = ReceiptCollection()
    unread_messages = []
    unread_counter = Counter()
    last_read_messages = {}
    for message, receipt in tuples:
        should_mark_delivered = mark_delivered and\
            (not receipt.is_delivered())
        should_mark_read = mark_read and\
            (not receipt.is_read())

        if should_mark_delivered:
            receipt.mark_as_delivered()
        if should_mark_read:
            receipt.mark_as_read()
            key = Conversation(message.conversationRecord).record.id.key
            unread_counter[key] += 1
            __update_last_read_messages(last_read_messages, message, key)

            print("new receipt,message_id=%s" %
                  (message.record.id.key))

        if should_mark_read or should_mark_delivered:
            new_receipts.append(receipt)
            unread_messages.append(message)

    return unread_messages, unread_counter, last_read_messages, new_receipts


def mark_messages(message_ids, mark_delivered, mark_read):
    """
    Check the receipt before saving.
    TODO: update this checking after role based ACL
    """
    user_id = current_user_id()
    messages = Message.fetch(message_ids)
    __validate_current_user_in_messages(messages, user_id)
    print("number of messages=%d" % (len(messages)))

    tuples = __get_messages_receipts(messages, user_id)
    unread_messages, unread_counter, last_read_messages, new_receipts = \
        __process_message_receipts(tuples,
                                   user_id,
                                   mark_delivered,
                                   mark_read)

    print("number of new receipts=%d" % (len(new_receipts)))
    new_receipts.save()

    with db.conn() as conn:
        __update_user_conversations(unread_counter, last_read_messages, conn)
        __update_and_notify_unread_messages(unread_messages, conn)


def handle_get_receipt(message_id):
    """
    Retrieve receipts for a message.
    """
    logging.info("handle_get_receipt: for message_id %s", message_id)
    message = Message.fetch(message_id)
    conversation = Conversation(message.conversationRecord)
    if not conversation.is_participant(current_user_id()):
        raise NotInConversationException()

    logging.debug(
        "handle_get_receipt: current user is conversation participant"
    )
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

    @skygear.op("chat:mark_as_last_read",
                auth_required=True,
                user_required=True)
    def mark_as_last_read_lambda(arg):
        if isinstance(arg, list) and is_str_list(arg):
            return handle_mark_as_read_by_range(arg)
        raise SkygearChatException('bad request')
