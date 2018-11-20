from skygear.models import Record, RecordID, Reference

from .database import Database
from .predicate import Predicate
from .query import Query
from .utils import _get_container


class ChatRecord(Record):
    record_type = None
    database_id = '_public'

    def save(self):
        database = self._get_database()
        database.save([self])

    def delete(self):
        database = self._get_database()
        database.delete([self])

    def to_record(self, record):
        record._id = self._id
        record._owner_id = self._owner_id
        record._acl = self._acl
        record._created_at = self._created_at
        record._created_by = self._created_by
        record._updated_at = self._updated_at
        record._updated_by = self._updated_by
        record._data = self._data

    @classmethod
    def delete_all(self, records):
        database = self._get_database()
        database.delete(records)

    @classmethod
    def save_all(self, records, atomic=True):
        database = self._get_database()
        database.save(records, atomic)

    @classmethod
    def _get_database(cls):
        return Database(_get_container(), cls.database_id)

    @classmethod
    def fetch_one(cls, key):
        result = cls.fetch_all([key])
        if len(result) == 0:
            return None
        return result[0]

    @classmethod
    def fetch_all(cls, keys):
        keys = [cls.__key_from_obj(key) for key in keys]
        database = cls._get_database()
        result = database.query(Query(cls.record_type,
                                      predicate=Predicate(_id__in=keys),
                                      limit=len(keys)))
        result = [cls.from_record(record) for record in result]
        return result

    @classmethod
    def exists(cls, record):
        return cls.fetch_one(record.id.key) is not None

    @classmethod
    def __key_from_obj(cls, obj):
        if isinstance(obj, Reference):
            obj = obj.recordID.key
        if isinstance(obj, RecordID):
            obj = obj.key
        return obj

    @classmethod
    def from_record(cls, record):
        record = cls(record.id,
                     record.owner_id,
                     record.acl,
                     created_at=record.created_at,
                     created_by=record.created_by,
                     updated_at=record.updated_at,
                     updated_by=record.updated_by,
                     data=record.data)
        return record
