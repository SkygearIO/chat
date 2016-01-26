import datetime
import uuid

import jsonpickle
import skygear
from skygear.container import SkygearContainer
from skygear.utils.context import current_user_id
from skygear.utils import db
from skygear import pubsub
from psycopg2.extensions import AsIs


container = SkygearContainer()
container.api_key = "my_skygear_key"
container.app_name = "my_skygear_app"
schema_name = "app_%s" % container.app_name


class SkygearChatException(Exception):
    pass


@skygear.before_save("conversation", async=False)
def handle_conversation_before_save(record, original_record, conn):
    if len(record['participant_ids']) == 0:
        raise SkygearChatException("no participants")

    if len(record['admin_ids']) == 0 and not record.get('is_direct_message'):
        raise SkygearChatException("no admin assigned")

    if original_record is not None:
        if current_user_id() not in original_record['admin_ids']:
            raise SkygearChatException("no permission to edit conversation")

    if original_record is None and record.get('is_direct_message'):
        if current_user_id() not in record['participant_ids']:
            raise SkygearChatException(
                "cannot create direct conversations for other users")

        if len(record['participant_ids']) != 2:
            raise SkygearChatException(
                "direct message must only have two participants")

        record['admin_ids'] = []


@skygear.after_save("conversation")
def handle_conversation_after_save(record, original_record, conn):
    if original_record is None:
        for p_id in record['participant_ids']:
            _publish_event(
                p_id, "conversation", "create",
                record, original_record)

    else:
        for p_id in set(record['participant_ids']
                + original_record['participant_ids']):
            _publish_event(
                p_id, "conversation", "update", record, original_record)


@skygear.before_delete("conversation", async=False)
def handle_conversation_before_delete(record, conn):
    if current_user_id() not in record['admin_ids']:
        raise SkygearChatException("no permission to delete conversation")


@skygear.after_delete("conversation")
def handle_conversation_after_delete(record, conn):
    for p_id in record['participant_ids']:
        _publish_event(
            p_id, "conversation", "delete", record)


@skygear.before_save("message", async=False)
def handle_message_before_save(record, original_record, conn):
    conversation = _get_conversation(record['conversation_id'])

    if current_user_id() not in conversation['participant_ids']:
        raise SkygearChatException("user not in conversation")

    if original_record is not None:
        raise SkygearChatException("message is not editable")


@skygear.after_save("message")
def handle_message_after_save(record, original_record, conn):
    conversation = _get_conversation(record['conversation_id'])

    if original_record is None:
        for p_id in conversation['participant_ids']:
            _publish_event(
                p_id, "message", "create", record)


@skygear.before_save("last_message_read", async=False)
def handle_last_message_read_before_save(record, original_record, conn):
    new_id = record.get('message_id')
    if new_id is None:
        return

    old_id = original_record and original_record.get('message_id')
    conversation_id = record['conversation_id']

    cur = conn.execute('''
        SELECT _id, _created_at
        FROM %(schema_name)s.message
        WHERE (_id = %(new_id)s OR _id = %(old_id)s)
        AND conversation_id = %(conversation_id)s
        LIMIT 2;
        ''', {
            'schema_name': AsIs(schema_name),
            'new_id': new_id,
            'old_id': old_id,
            'conversation_id': conversation_id
        }
    )

    results = {}
    for row in cur:
        results[row[0]] = row[1]

    if new_id not in results:
        raise SkygearChatException("no message found")

    if old_id and results[new_id] < results[old_id]:
        raise SkygearChatException("the updated message is older")


@skygear.op("chat:get_messages", auth_required=True, user_required=True)
def get_messages(conversation_id, limit, before_time=None):
    conversation = _get_conversation(conversation_id)

    if current_user_id() not in conversation['participant_ids']:
        raise SkygearChatException("user not in conversation")

    with db.conn() as conn:
        cur = conn.execute('''
            SELECT _id, _created_at, _created_by, body, conversation_id
            FROM %(schema_name)s.message
            WHERE conversation_id = %(conversation_id)s
            AND (_created_at < %(before_time)s OR %(before_time)s IS NULL)
            ORDER BY _created_at DESC
            LIMIT %(limit)s;
            ''', {
                'schema_name': AsIs(schema_name),
                'conversation_id': conversation_id,
                'before_time': before_time,
                'limit': limit
            }
        )

        results = []
        for row in cur:
            results.append({
                '_id': row[0],
                '_created_at': row[1].isoformat(),
                '_created_by': row[2],
                'body': row[3],
                'conversation_id': row[4]
            })

        return {'results': results}


@skygear.op("chat:get_unread_message_count",
    auth_required=True, user_required=True)
def get_unread_message_count(conversation_id):
    with db.conn() as conn:
        cur = conn.execute('''
            SELECT message_id
            FROM %(schema_name)s.last_message_read
            WHERE conversation_id = %(conversation_id)s
            AND _database_id = %(user_id)s
            LIMIT 1;
            ''', {
                'schema_name': AsIs(schema_name),
                'conversation_id': conversation_id,
                'user_id': current_user_id()
            }
        )

        results = [row[0] for row in cur]

        if results:
            message_id = results[0]
        else:
            message_id = None

        if message_id:
            cur = conn.execute('''
                SELECT COUNT(*)
                FROM %(schema_name)s.message
                WHERE _created_at > (
                    SELECT _created_at
                    FROM %(schema_name)s.message
                    WHERE _id = %(message_id)s
                )
                AND conversation_id = %(conversation_id)s
                ''', {
                    'schema_name': AsIs(schema_name),
                    'message_id': message_id,
                    'conversation_id': conversation_id
                }
            )
        else:
            cur = conn.execute('''
                SELECT COUNT(*)
                FROM %(schema_name)s.message
                WHERE conversation_id = %(conversation_id)s
                ''', {
                    'schema_name': AsIs(schema_name),
                    'conversation_id': conversation_id
                }
            )

    return {'count': [row[0] for row in cur][0]}


def _get_conversation(conversation_id):
    data = {
        'database_id': '_public',
        'record_type': 'conversation',
        'limit': 1,
        'sort': [],
        'include': {},
        'count': False,
        'predicate': [
        'eq', {
            '$type': 'keypath',
            '$val': '_id'
        },
        conversation_id]
    }

    response = skygear.container.send_action(
        container._request_url('record:query'),
        container._payload('record:query', data)
    )

    if len(response['result']) == 0:
        raise SkygearChatException("no conversation found")

    return response['result'][0]


def _publish_event(participant_id, record_type, event_type, record,
        original_record=None):
    data = {
        'record_type': record_type,
        'event_type': event_type,
        'record': jsonpickle.encode(record, unpicklable=False),
        'original_record': jsonpickle.encode(
            original_record, unpicklable=False)
    }

    channel_name = _get_channel_by_user_id(participant_id)

    if channel_name:
        pubsub.publish(channel_name, data)


def _get_channel_by_user_id(user_id):
    with db.conn() as conn:
        cur = conn.execute('''
            SELECT name
            FROM %(schema_name)s.user_channel
            WHERE _owner_id = %(user_id)s
            LIMIT 1;
            ''', {
                'schema_name': AsIs(schema_name),
                'user_id': user_id
            }
        )

        results = []
        for row in cur:
            results.append(row[0])

        if len(results) > 0:
            return results[0]
