import os

from psycopg2.extensions import AsIs

from skygear.container import SkygearContainer
from skygear.models import RecordID, Reference
from skygear.options import options
from skygear.utils import db

from .exc import SkygearChatException

container = SkygearContainer()
opts = vars(options)
container.api_key = os.getenv('API_KEY', opts.get('apikey'))
container.app_name = os.getenv('APP_NAME', opts.get('appname'))
schema_name = "app_%s" % container.app_name

MASTER_KEY = os.getenv('MASTER_KEY', opts.get('masterkey'))


def _get_conversation(conversation_id):
    # conversation_id can be Reference, recordID or string
    if isinstance(conversation_id, Reference):
        conversation_id = conversation_id.recordID.key
    if isinstance(conversation_id, RecordID):
        conversation_id = conversation_id.key
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

    response = container.send_action('record:query', data)

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
            'schema_name': AsIs(schema_name),
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
            'name': schema_name + "." + tablename,
        })
        results = []
        for row in cur:
            if row[0] is not None:
                results.append(row[0])

        return len(results) > 0
