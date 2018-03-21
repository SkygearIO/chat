from psycopg2.extensions import AsIs
from strict_rfc3339 import timestamp_to_rfc3339_utcoffset

from skygear.container import SkygearContainer
from skygear.options import options as skyoptions
from skygear.utils import db
from skygear.utils.context import current_context, current_user_id


def _get_container():
    return SkygearContainer(api_key=skyoptions.masterkey,
                            user_id=current_user_id())


def _get_schema_name():
    return "app_%s" % skyoptions.appname


def _get_channels_by_user_ids(user_ids):
    # TODO: use database.query instead of raw SQL
    with db.conn() as conn:
        cur = conn.execute('''
            SELECT name
            FROM %(schema_name)s.user_channel
            WHERE _owner_id in %(user_ids)s
            LIMIT %(len)s;
            ''', {
            'schema_name': AsIs(_get_schema_name()),
            'user_ids': tuple(user_ids),
            'len': len(user_ids),
        }
        )

        results = []
        for row in cur:
            results.append(row[0])

        return results


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
