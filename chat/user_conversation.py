import hashlib
import uuid

from psycopg2.extensions import AsIs

import skygear
from skygear.models import Record, RecordID, Reference
from skygear.utils import db
from skygear.utils.context import current_user_id

from .predicate import Predicate
from .query import Query
from .record import ChatRecord
from .utils import _get_schema_name


class UserConversation(ChatRecord):
    record_type = 'user_conversation'

    @classmethod
    def new(cls, conversation, user_id):
        record = cls(None,
                     user_id,
                     conversation.get_user_conversation_acl())
        record['user'] = Reference(RecordID('user', user_id))
        record['conversation'] = Reference(conversation.id)
        record['unread_count'] = 0
        record['is_admin'] = False
        return record

    def get_hash(self):
        return UserConversation.\
               get_consistent_hash(self['conversation'].recordID.key,
                                   self['user'].recordID.key)

    def mark_admin(self, flag):
        database = self._get_database()
        record = Record(self.id, self.owner_id, self.acl)
        record['is_admin'] = flag
        record['user'] = self['user']
        record['conversation'] = self['conversation']
        database.save([record])

    @classmethod
    def get_consistent_hash(cls, conversation_id, user_id):
        seed = conversation_id + user_id
        sha = hashlib.sha256(bytes(seed, 'utf8'))
        return str(uuid.UUID(bytes=sha.digest()[0:16]))

    @property
    def id(self):
        return RecordID(self.record_type, self.get_hash())

    @classmethod
    def exists(cls, record, check_is_admin=False):
        record = cls.fetch_one(record.id.key)
        return (record is not None) and\
               (not check_is_admin or record['is_admin'])

    @classmethod
    def fetch_all_with_paging(cls, page, page_size, order='desc'):
        database = cls._get_database()
        offset = (page - 1) * page_size
        query_result = database.query(
                       Query(cls.record_type,
                             predicate=Predicate(user__eq=current_user_id()),
                             offset=offset,
                             limit=page_size,
                             include=["conversation", "user"])
                       .add_order('_updated_at', order))
        return [uc for uc in query_result]

    @classmethod
    def fetch_all_by_conversation_id(cls, conversation_id):
        database = cls._get_database()
        predicate = Predicate(conversation__eq=conversation_id)
        records = database.query(Query(cls.record_type,
                                       predicate=predicate,
                                       include=["conversation", "user"],
                                       limit=None))
        return [UserConversation.from_record(record) for record in records]

    @classmethod
    def fetch_one(cls,
                  conversation_id,
                  user_id=None):
        database = cls._get_database()
        if user_id is None:
            user_id = current_user_id()
        predicate = Predicate(user__eq=user_id,
                              conversation__eq=conversation_id)
        query_result = database.query(
                       Query(cls.record_type,
                             predicate=predicate,
                             limit=1,
                             include=["conversation", "user"]))
        return UserConversation.from_record(query_result[0])\
            if len(query_result) == 1 else None


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
