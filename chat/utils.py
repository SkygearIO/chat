from psycopg2.extensions import AsIs
from strict_rfc3339 import timestamp_to_rfc3339_utcoffset

from skygear.container import SkygearContainer
from skygear.models import RecordID, Reference
from skygear.options import options as skyoptions
from skygear.utils import db
from skygear.utils.context import current_context

from .exc import SkygearChatException


def _get_schema_name():
    return "app_%s" % skyoptions.appname


def _get_conversation(conversation_id):
    # conversation_id can be Reference, recordID or string
    if isinstance(conversation_id, Reference):
        conversation_id = conversation_id.recordID.key
    if isinstance(conversation_id, RecordID):
        conversation_id = conversation_id.key

    container = SkygearContainer(api_key=skyoptions.apikey)
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


def current_context_has_master_key():
    # FIXME: skygear-server does not pass access_key_type information
    # yet. This is a temporary workaround before skygear-server has support.
    return 'access_key_type' not in current_context() or \
        current_context().get('access_key_type', '') == 'master'


def is_str_list(list_):
    if not isinstance(list_, list):
        return False
    for item in list_:
        if not isinstance(item, str):
            return False
    return True


def to_rfc3339_or_none(dt):
    if not dt:
        return None
    return timestamp_to_rfc3339_utcoffset(dt.timestamp())


def get_key_from_object(obj):
    if isinstance(obj, Reference):
        return obj.recordID.key
    if isinstance(obj, RecordID):
        return obj.key
    if isinstance(obj, str):
        return obj
    raise ValueError()


def fetch_records(container, database_id, record_type, ids, convert_func):
    """
    Fetch records with record API
    TODO: move to pyskygear
    """
    ids = list(set(ids))
    response = container.send_action(
            'record:query',
            {
                'database_id': database_id,
                'record_type': record_type,
                'limit': len(ids),
                'sort': [],
                'count': False,
                'predicate': [
                    'in', {
                        '$type': 'keypath',
                        '$val': '_id'
                    },
                    ids
                ]
            }
        )

    if 'error' in response:
        raise SkygearChatException(response['error'])

    results = []
    for result in response['result']:
        results.append(convert_func(result))

    return results
