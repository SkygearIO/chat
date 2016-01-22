import datetime

import skygear
from skygear.container import SkygearContainer
from skygear.utils.context import current_user_id
from skygear.utils import db


container = SkygearContainer()
container.api_key = "my_skygear_key"
container.app_name = "my_skygear_app"


@skygear.before_save("conversation", async=False)
def handle_conversation_before_save(new_record, old_record, db):
    # TODO: check user exists

    if len(new_record['participant_ids']) == 0:
        raise Exception("no participants")

    if len(new_record['admin_ids']) == 0:
        raise Exception("no admin assigned")

    if old_record is not None:
        if current_user_id() not in old_record['admin_ids']:
            raise Exception("no permission to edit conversation")


@skygear.before_delete("conversation", async=False)
def handle_conversation_before_delete(record, db):
    if current_user_id() not in record['admin_ids']:
        raise Exception("no permission to delete conversation")


@skygear.before_save("message", async=False)
def handle_message_before_save(new_record, old_record, db):
    conversation = _get_conversation(new_record['conversation_id'])

    if current_user_id() not in conversation['participant_ids']:
        raise Exception("user not in conversation")

    if old_record is not None:
        raise Exception("message is not editable")


@skygear.op("chat:get_messages", auth_required=True, user_required=True)
def get_messages(conversation_id, limit, before_time=None):
    conversation = _get_conversation(conversation_id)

    if current_user_id() not in conversation['participant_ids']:
        raise Exception("user not in conversation")

    with db.conn() as conn:
        cur = conn.execute('''
            SELECT _id, _created_at, _created_by, body, conversation_id
            FROM app_my_skygear_app.message
            WHERE conversation_id = %s
            AND (_created_at < %s OR %s IS NULL)
            ORDER BY _created_at DESC
            LIMIT %s;
            ''', (conversation_id, before_time, before_time, limit)
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


def _get_conversation(conversation_id):
    data = {
        'database_id': '_public',
        'record_type': 'conversation',
        'limit': 50,
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
        raise Exception("no conversation found")

    return response['result'][0]
