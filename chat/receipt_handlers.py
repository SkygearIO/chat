import logging

import skygear
from skygear.models import Record
from skygear.utils.context import current_user_id

from .conversation import Conversation
from .exc import NotInConversationException, SkygearChatException
from .message import Message
from .receipt import create_delivered_receipts, create_read_receipts
from .utils import is_str_list


def _message_status_may_change(
    new_receipt: Record,
    old_receipt: Record
) -> bool:
    """
    Return true if the message status of a message may change. This
    is used to prevent status to change unnecessarily.
    """
    if not old_receipt:
        return True

    return new_receipt.get('read_at', None) != old_receipt.get('read_at', None)


def handle_receipt_before_save(record, original_record, conn):
    """
    Check the receipt before saving.
    """
    message_ref = record.get('message', '')
    if not message_ref:
        raise SkygearChatException('missing message')

    message = Message.fetch(message_ref.recordID.key)
    conversation = Conversation(message.conversationRecord)
    if not conversation.is_participant(current_user_id()):
        raise NotInConversationException()

    user_ref = record.get('user', None)
    if not user_ref or user_ref.recordID.key != current_user_id():
        raise SkygearChatException('argument exception')

    if original_record:
        # Prevent the client from modifying the delivered_at and read_at fields
        # if a value exists.
        if original_record.get('delivered_at', None):
            record['delivered_at'] = original_record['delivered_at']
        if original_record.get('read_at', None):
            record['read_at'] = original_record['read_at']


def handle_receipt_after_save(record, original_record, conn):
    """
    Handle further update or notification after saving a receipt.
    """
    logging.debug(
        'handle_receipt_after_save: has original_record %s',
        bool(original_record)
    )
    logging.debug(
        'handle_receipt_after_save: record.read_at %s',
        record.get('read_at', None)
    )
    if original_record:
        logging.debug(
            'handle_receipt_after_save: original_record.read_at %s',
            original_record.get('read_at', None)
        )

    if _message_status_may_change(record, original_record):
        logging.debug(
            'updating message status because receipt read_at has changed'
        )
        message = Message.fetch(record['message'].recordID.key)
        message.updateMessageStatus(conn)
        message.notifyParticipants()


def handle_mark_as_delivered(message_ids: [str]):
    """
    Marking a message as delivered, which should update a receipt for the
    message.
    """
    logging.debug(
        'handle_mark_as_delivered: message_ids: %s',
        ','.join(message_ids)
    )

    receipts = create_delivered_receipts(current_user_id(), message_ids)
    receipts.save()


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

    receipts = create_read_receipts(current_user_id(), message_ids)
    receipts.save()


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
        return handle_receipt_before_save(record, original_record, conn)

    @skygear.after_save("receipt", async=True)
    def receipt_after_save_handler(record, original_record, conn):
        return handle_receipt_after_save(record, original_record, conn)


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
