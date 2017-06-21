from psycopg2.extensions import AsIs
from psycopg2.extras import Json
from strict_rfc3339 import timestamp_to_rfc3339_utcoffset

import skygear
from skygear.transmitter.encoding import serialize_record
from skygear.utils import db
from skygear.utils.context import current_user_id

from .asset import sign_asset_url
from .conversation import Conversation
from .exc import (AlreadyDeletedException, MessageNotFoundException,
                  NotInConversationException, NotSupportedException)
from .message import Message
from .message_history import MessageHistory
from .utils import _get_conversation, _get_schema_name


def get_messages(conversation_id, limit, before_time=None):
    conversation = Conversation(_get_conversation(conversation_id))
    if not conversation.is_participant(current_user_id()):
        raise NotInConversationException()

    with db.conn() as conn:
        cur = conn.execute('''
            SELECT
                _id, _created_at, _created_by,
                body, conversation, metadata, message_status,
                attachment
            FROM %(schema_name)s.message
            WHERE conversation = %(conversation_id)s
            AND (_created_at < %(before_time)s OR %(before_time)s IS NULL)
            AND deleted = false
            ORDER BY _created_at DESC
            LIMIT %(limit)s;
            ''', {
                'schema_name': AsIs(_get_schema_name()),
                'conversation_id': conversation_id,
                'before_time': before_time,
                'limit': limit
            }
        )

        results = cursor_to_messages(cur)
        return {'results': results}


def get_messages_by_ids(message_ids):
    '''
    Return the array of message with gived ids.

    - ACL check will rely on the `participant_ids` of referenced conversation.
    - For id does not have corresponding message, no error will be reported.
    - For message that user have no access to, no error will be reported.
    '''
    with db.conn() as conn:
        cur = conn.execute('''
            SELECT
                m._id, m._created_at, m._created_by,
                m.body, m.conversation,
                m.metadata, m.message_status,
                m.attachment
            FROM %(schema_name)s.message AS m
            LEFT JOIN %(schema_name)s.conversation
            ON m.conversation=conversation._id
            WHERE m._id = ANY(%(ids)s)
            AND conversation.participant_ids @> %(user_id)s
            ''', {
                'schema_name': AsIs(_get_schema_name()),
                'ids': message_ids,
                'user_id': Json(current_user_id())
            }
        )

        results = cursor_to_messages(cur)
        return {
            'results': results
        }


def cursor_to_messages(cur):
    results = []
    for row in cur:
        created_stamp = row[1].timestamp()
        dt = timestamp_to_rfc3339_utcoffset(created_stamp)
        r = {
            '_id': 'message/' + row[0],
            '_created_at': dt,
            '_created_by': row[2],
            'body': row[3],
            'conversation': {
                '$id': 'conversation/' + row[4],
                '$type': 'ref'
            },
            'metadata': row[5],
            'message_status': row[6],
        }
        if row[7]:
            r['attachment'] = {
                '$type': 'asset',
                '$name': row[7],
                '$url': sign_asset_url(row[7])
            }
        results.append(r)
    return results


def handle_message_before_save(record, original_record, conn):
    message = Message.from_record(record)
    conversation = Conversation(message.fetchConversationRecord())
    if not conversation.is_participant(current_user_id()):
        raise NotInConversationException()

    if original_record is not None and original_record['deleted']:
        raise AlreadyDeletedException()

    if original_record is None:
        message.record['deleted'] = False
        message.record['revision'] = 1
    else:
        message_history = MessageHistory(Message.from_record(original_record))
        message_history.save()

    if message.record.get('message_status', None) is None:
        message.record['message_status'] = 'delivered'

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

    @skygear.op("chat:get_messages_by_ids", auth_required=True,
                user_required=True)
    def get_messages_by_ids_lambda(message_ids):
        return get_messages_by_ids(message_ids)

    @skygear.op("chat:delete_message", auth_required=True, user_required=True)
    def delete_message_lambda(message_id):
        return delete_message(message_id)
