import hashlib
import uuid

from psycopg2.extensions import AsIs

import skygear
from skygear.container import SkygearContainer
from skygear.models import (ACCESS_CONTROL_ENTRY_LEVEL_WRITE, Record, RecordID,
                            Reference, RoleAccessControlEntry)
from skygear.options import options as skyoptions
from skygear.utils import db
from skygear.utils.context import current_user_id

from .conversation import get_admin_role, get_participant_role
from .database import Database
from .predicate import Predicate
from .query import Query
from .utils import _get_schema_name


class UserConversation(Record):
    def __init__(self, conversation, user):
        super(self.__class__, self).\
            __init__(None, user, [RoleAccessControlEntry(
                                 get_admin_role(conversation),
                                 ACCESS_CONTROL_ENTRY_LEVEL_WRITE),
                                 RoleAccessControlEntry(
                                 get_participant_role(conversation),
                                 ACCESS_CONTROL_ENTRY_LEVEL_WRITE)])
        self['user'] = Reference(RecordID('user', user))
        self['conversation'] = Reference(RecordID('conversation',
                                                  conversation))
        self['unread_count'] = 0
        self['is_admin'] = False

    @staticmethod
    def get_consistent_hash(conversation_id, user_id):
        seed = conversation_id + user_id
        sha = hashlib.sha256(bytes(seed, 'utf8'))
        return str(uuid.UUID(bytes=sha.digest()[0:16]))

    @property
    def id(self):
        hash_key = UserConversation.\
                   get_consistent_hash(self['conversation'].recordID.key,
                                       self['user'].recordID.key)
        return RecordID('user_conversation', hash_key)


def is_user_id_in_conversation(user_id, conversation_id, check_is_admin=False):
    container = SkygearContainer(api_key=skyoptions.masterkey,
                                 user_id=user_id)
    database = Database(container, '_public')
    query = Query('user_conversation',
                  predicate=Predicate(
                            conversation__eq=conversation_id,
                            user__eq=user_id),
                  limit=1)
    result = database.query(query)
    print("is_user_id_in_conversation", result)
    return len(result["result"]) == 1 and\
              (not check_is_admin or result["result"][0]['is_admin'])


def total_unread(user_id=None):
    if user_id is None:
        user_id = current_user_id()
    with db.conn() as conn:
        cur = conn.execute('''
            SELECT COUNT(*), SUM("unread_count")
            FROM %(schema_name)s.user_conversation
            WHERE
                "unread_count" > 0 AND
                "user" = %(user_id)s
            ''', {
                'schema_name': AsIs(_get_schema_name()),
                'user_id': user_id
            }
        )
        r = cur.first()
        conversation_count = r[0]
        message_count = r[1]
    return {
        'conversation': conversation_count,
        'message': message_count
    }


def register_user_conversation_lambdas(settings):
    @skygear.op("chat:total_unread", auth_required=True, user_required=True)
    def total_unread_lambda():
        return total_unread()
