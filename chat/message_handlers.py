from psycopg2.extensions import AsIs
from strict_rfc3339 import timestamp_to_rfc3339_utcoffset

import skygear
from skygear.utils import db
from skygear.utils.context import current_user_id

from .asset import sign_asset_url
from .conversation import Conversation
from .exc import NotInConversationException, SkygearChatException
from .message import Message
from .pubsub import _publish_record_event
from .utils import (_get_conversation, _get_schema_name,
                    current_context_has_master_key)


def get_messages(conversation_id, limit, before_time=None):
    conversation = Conversation(_get_conversation(conversation_id))
    if not conversation.is_participant(current_user_id()):
        raise NotInConversationException()

    # FIXME: After the ACL can be by-pass the ACL, we should query the with
    # master key
    # https://github.com/SkygearIO/skygear-server/issues/51
    with db.conn() as conn:
        cur = conn.execute('''
            SELECT
                _id, _created_at, _created_by,
                body, conversation_id, metadata, attachment
            FROM %(schema_name)s.message
            WHERE conversation_id = %(conversation_id)s
            AND (_created_at < %(before_time)s OR %(before_time)s IS NULL)
            ORDER BY _created_at DESC
            LIMIT %(limit)s;
            ''', {
                'schema_name': AsIs(_get_schema_name()),
                'conversation_id': conversation_id,
                'before_time': before_time,
                'limit': limit
            }
        )

        results = []
        for row in cur:
            created_stamp = row[1].timestamp()
            dt = timestamp_to_rfc3339_utcoffset(created_stamp)
            r = {
                '_id': 'message/' + row[0],
                '_created_at': dt,
                '_created_by': row[2],
                'body': row[3],
                'conversation_id': {
                    '$id': 'conversation/' + row[4],
                    '$type': 'ref'
                },
                'metadata': row[5],
            }
            if row[6]:
                r['attachment'] = {
                    '$type': 'asset',
                    '$name': row[6],
                    '$url': sign_asset_url(row[6])
                }
            results.append(r)

        return {'results': results}


def handle_message_before_save(record, original_record, conn):
    message = Message.from_record(record)
    conversation = Conversation(message.fetchConversationRecord())
    if not conversation.is_participant(current_user_id()):
        raise NotInConversationException()

    if original_record is not None and not current_context_has_master_key():
        raise SkygearChatException("message is not editable")

    if original_record is not None:
        message.updateConversationStatus()

    return message.record


def handle_message_after_save(record, original_record, conn):
    message = Message.from_record(record)
    event_type = 'create' if original_record is None else 'update'
    conversation = Conversation(message.fetchConversationRecord())
    for p_id in conversation.get_participant_set():
        _publish_record_event(
            p_id, "message", event_type, record, original_record)

    if original_record is None:
        # Update all UserConversation unread count by 1
        conversation_id = record['conversation_id'].recordID.key
        conn.execute('''
            UPDATE %(schema_name)s.user_conversation
            SET "unread_count" = "unread_count" + 1
            WHERE "conversation" = %(conversation_id)s
        ''', {
            'schema_name': AsIs(_get_schema_name()),
            'conversation_id': conversation_id
        })


def register_message_hooks(settings):
    @skygear.before_save("message", async=False)
    def message_before_save_handler(record, original_record, conn):
        return handle_message_before_save(record, original_record, conn)

    @skygear.after_save("message")
    def message_after_save_handler(record, original_record, conn):
        return handle_message_after_save(record, original_record, conn)


def register_message_lambdas(settings):
    @skygear.op("chat:get_messages", auth_required=True, user_required=True)
    def get_messages_lambda(conversation_id, limit, before_time=None):
        return get_messages(conversation_id, limit, before_time)
