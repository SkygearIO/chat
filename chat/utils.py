from psycopg2.extensions import AsIs

from skygear.container import SkygearContainer
from skygear.models import RecordID, Reference
from skygear.skyconfig import config as skygear_config
from skygear.utils import db

from .exc import SkygearChatException


def _get_schema_name():
    return "app_%s" % skygear_config.app.name


def _get_conversation(conversation_id):
    # conversation_id can be Reference, recordID or string
    if isinstance(conversation_id, Reference):
        conversation_id = conversation_id.recordID.key
    if isinstance(conversation_id, RecordID):
        conversation_id = conversation_id.key

    container = SkygearContainer(api_key=skygear_config.app.api_key)
    response = container.send_action(
        'record:query',
        {
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
                conversation_id
            ]
        }
    )

    if 'error' in response:
        raise SkygearChatException(response['error'])

    if len(response['result']) == 0:
        raise SkygearChatException("no conversation found")

    return response['result'][0]


def _get_channel_by_user_id(user_id):
    if not _check_if_table_exists('user_channel'):
        return None

    with db.conn() as conn:
        cur = conn.execute('''
            SELECT name
            FROM %(schema_name)s.user_channel
            WHERE _owner_id = %(user_id)s
            LIMIT 1;
            ''', {
            'schema_name': AsIs(_get_schema_name()),
            'user_id': user_id
        }
        )

        results = []
        for row in cur:
            results.append(row[0])

        if len(results) > 0:
            return results[0]


def _check_if_table_exists(tablename):
    with db.conn() as conn:
        cur = conn.execute('''
            SELECT to_regclass(%(name)s)
            ''', {
            'name': _get_schema_name() + "." + tablename,
        })
        results = []
        for row in cur:
            if row[0] is not None:
                results.append(row[0])

        return len(results) > 0
