from psycopg2.extensions import AsIs

import skygear
from skygear.transmitter.encoding import serialize_record
from skygear.utils import db
from skygear.utils.context import current_user_id

from .conversation import Conversation, get_message_acl
from .database import Database
from .exc import (AlreadyDeletedException, MessageNotFoundException,
                  NotInConversationException, NotSupportedException)
from .message import Message
from .message_history import MessageHistory
from .predicate import Predicate
from .query import Query
from .user_conversation import is_user_id_in_conversation
from .utils import _get_container, _get_schema_name


def get_messages(conversation_id, limit, before_time=None):
    if not is_user_id_in_conversation(current_user_id(), conversation_id):
        raise NotInConversationException()
    database = Database(_get_container(), '_public')
    predicate = Predicate(conversation__eq=conversation_id, deleted__eq=False)
    if before_time is not None:
        predicate = predicate & Predicate(_created_at__lt=before_time)
    query = Query('message', predicate=predicate, limit=limit)
    query.add_order('_created_at', 'desc')
    return {'results': database.query(query)["result"]}


def handle_message_before_save(record, original_record, conn):
    message = Message.from_record(record)

    if original_record is not None and original_record['deleted']:
        raise AlreadyDeletedException()

    if not is_user_id_in_conversation(current_user_id(),
                                      message.conversation_id):
        raise NotInConversationException()

    if original_record is None:
        message.record['deleted'] = False
        message.record['revision'] = 1
    else:
        message_history = MessageHistory(Message.from_record(original_record))
        message_history.save()

    if message.record.get('message_status', None) is None:
        message.record['message_status'] = 'delivered'
    # TODO use proper ACL setter
    message.record._acl = get_message_acl(message.conversation_id)
    return message.record


def handle_message_after_save(record, original_record, conn):
    message = Message.from_record(record)

    event_type = 'create'
    if original_record is not None:
        event_type = 'update'
    if record.get('deleted', False):
        event_type = 'delete'

    message.notifyParticipants(event_type)

    if original_record is None:
        # Update all UserConversation unread count by 1
        conversation_id = record['conversation'].recordID.key
        conn.execute('''
            UPDATE %(schema_name)s.user_conversation
            SET
                "unread_count" = "unread_count" + 1,
                "_updated_at" = CURRENT_TIMESTAMP
            WHERE
                "conversation" = %(conversation_id)s
                AND "user" != %(user_id)s
        ''', {
            'schema_name': AsIs(_get_schema_name()),
            'conversation_id': conversation_id,
            'user_id': current_user_id()
        })
        conn.execute('''
            UPDATE %(schema_name)s.conversation
            SET "last_message" = %(message_id)s
            WHERE "_id" = %(conversation_id)s
        ''', {
            'schema_name': AsIs(_get_schema_name()),
            'conversation_id': conversation_id,
            'message_id': record.id.key
        })


def _get_new_last_message_id(conn, message):
    cur = conn.execute('''
            SELECT _id FROM %(schema_name)s.message
            WHERE deleted = false AND seq < %(seq)s
            ORDER BY seq DESC LIMIT 1
        ''', {
            'schema_name': AsIs(_get_schema_name()),
            'seq': message.record['seq']
        })
    row = cur.fetchone()
    return None if row is None else row['_id']


def _update_conversation_last_message(conn, conversation, last_message,
                                      new_last_message_id):
    last_message_key = 'message/' + last_message.record.id.key
    if last_message_key == conversation.record['last_message']['$id']:
        conversation_id = last_message.record['conversation'].recordID.key
        conn.execute('''
        UPDATE %(schema_name)s.conversation
        SET last_message = %(new_last_message_id)s
        WHERE _id = %(conversation_id)s
        ''', {
            'schema_name': AsIs(_get_schema_name()),
            'conversation_id': conversation_id,
            'new_last_message_id': new_last_message_id
        })


def _update_user_conversation_last_read_message(conn, last_message,
                                                new_last_message_id):
    conn.execute('''
    UPDATE %(schema_name)s.user_conversation
    SET last_read_message = %(new_last_message_id)s
    WHERE last_read_message = %(old_last_message_id)s
    ''', {
        'schema_name': AsIs(_get_schema_name()),
        'new_last_message_id': new_last_message_id,
        'old_last_message_id': last_message.record.id.key
    })


def delete_message(message_id):
    '''
    Delete a message
    - Soft-delete message from record
    - Update last_message and last_read_message
    '''
    message = Message.fetch(message_id)
    if message is None:
        raise MessageNotFoundException()

    message.delete()
    record = serialize_record(message.record)

    with db.conn() as conn:
        new_last_message_id = _get_new_last_message_id(conn, message)
        conversation = Conversation(message.fetchConversationRecord())
        _update_conversation_last_message(conn, conversation, message,
                                          new_last_message_id)
        _update_user_conversation_last_read_message(conn, message,
                                                    new_last_message_id)
    return record


def register_message_hooks(settings):
    @skygear.before_save("message", async=False)
    def message_before_save_handler(record, original_record, conn):
        return handle_message_before_save(record, original_record, conn)

    @skygear.after_save("message")
    def message_after_save_handler(record, original_record, conn):
        return handle_message_after_save(record, original_record, conn)

    @skygear.before_delete("message", async=False)
    def message_before_delete_handler(record, original_record, conn):
        raise NotSupportedException()


def register_message_lambdas(settings):
    @skygear.op("chat:get_messages", auth_required=True, user_required=True)
    def get_messages_lambda(conversation_id, limit, before_time=None):
        return get_messages(conversation_id, limit, before_time)

    @skygear.op("chat:delete_message", auth_required=True, user_required=True)
    def delete_message_lambda(message_id):
        return delete_message(message_id)
