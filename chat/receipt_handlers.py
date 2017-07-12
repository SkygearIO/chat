import logging

import skygear
from skygear.utils import db
from skygear.utils.context import current_user_id

from .conversation import Conversation
from .exc import (NotInConversationException, NotSupportedException,
                  SkygearChatException)
from .message import Message
from .receipt import Receipt, ReceiptCollection
from .utils import current_context_has_master_key, is_str_list


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


def __validate_current_user_in_messages(messages, user_id):
    for message in messages:
        conversation = Conversation(message.conversationRecord)
        if not conversation.is_participant(user_id):
            print("user %s is not a participant in conversation %s" %
                  (user_id, conversation.recordID.key))
            raise NotInConversationException()


def __update_and_notify_unread_messages(messages):
    with db.conn() as conn:
        for message in messages:
            message.updateMessageStatus(conn)
            message.notifyParticipants()


def __fetch_receipts(messages, user_id):
    receipt_ids = [Receipt.consistent_id(user_id,
                   message.record.id.key)
                   for message in messages]

    found_receipts = {x.record.id.key: x for x in Receipt.fetch(receipt_ids)}
    return found_receipts


def mark_messages(message_ids, mark_delivered, mark_read):
    """
    Check the receipt before saving.
    TODO: update this checking after role based ACL
    """
    user_id = current_user_id()
    messages = Message.fetch(message_ids)
    __validate_current_user_in_messages(messages, user_id)
    found_receipts = __fetch_receipts(messages, user_id)

    new_receipts = ReceiptCollection()
    unread_messages = []
    for message in messages:
        message_id = message.record.id.key
        receipt_id = Receipt.consistent_id(user_id, message_id)
        receipt = found_receipts.get(receipt_id, None)
        if receipt is None:
            receipt = Receipt(user_id, message_id)

        should_mark_delivered = mark_delivered and\
            (not receipt.is_delivered())
        should_mark_read = mark_read and\
            (not receipt.is_read())

        if should_mark_read or should_mark_delivered:

            if should_mark_delivered:
                receipt.mark_as_delivered()

            if should_mark_read:
                receipt.mark_as_read()

            print("new receipt,user_id=%s,message_id=%s" %
                  (user_id, message_id))

            new_receipts.append(receipt)
            unread_messages.append(message)

    new_receipts.save()
    __update_and_notify_unread_messages(unread_messages)


def handle_get_receipt(message_id):
    """
    Retrieve receipts for a message.
    """
    logging.info("handle_get_receipt: for message_id %s", message_id)
    messages = Message.fetch(message_id)
    if len(messages) == 0:
        raise SkygearChatException('Message not found')
    message = messages[0]
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
