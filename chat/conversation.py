from skygear.models import (ACCESS_CONTROL_ENTRY_LEVEL_READ,
                            ACCESS_CONTROL_ENTRY_LEVEL_WRITE, RecordID,
                            RoleAccessControlEntry)

from .database import Database
from .exc import SkygearChatException
from .predicate import Predicate
from .query import Query
from .record import ChatRecord
from .user_conversation import UserConversation


class Conversation(ChatRecord):
    record_type = 'conversation'

    def mark_non_distinct(self):
        database = self._get_database()
        database.save([{'_id': Database._encode_id(self.id),
                        'distinct_by_participants': True}])

    @classmethod
    def equal_record(cls, record1, record2):
        keys = ['distinct_by_participants', 'title', 'meta']
        for key in keys:
            if ((key in record1) != (key in record2)) or \
               (key in record1 and record1[key] != record2[key]):
                return False
        return True

    @classmethod
    def new(cls, conversation_id, user_id):
        return Conversation(RecordID(cls.record_type, conversation_id),
                            user_id,
                            [RoleAccessControlEntry(
                             cls.get_admin_role(conversation_id),
                             ACCESS_CONTROL_ENTRY_LEVEL_WRITE),
                             RoleAccessControlEntry(
                             cls.get_participant_role(conversation_id),
                             ACCESS_CONTROL_ENTRY_LEVEL_READ)])

    @classmethod
    def get_participant_role(cls, conversation_id):
        return "%s-participant-%s" % (cls.record_type, conversation_id)

    @classmethod
    def get_admin_role(cls, conversation_id):
        return "%s-admin-%s" % (cls.record_type, conversation_id)

    def get_user_conversation_acl(self):
        return [RoleAccessControlEntry(
                self.get_admin_role(self.id.key),
                ACCESS_CONTROL_ENTRY_LEVEL_WRITE),
                RoleAccessControlEntry(
                self.get_participant_role(self.id.key),
                ACCESS_CONTROL_ENTRY_LEVEL_WRITE)]

    @classmethod
    def __uc_to_conversation(cls, uc):
        c = uc['_transient']['conversation']
        c['unread_count'] = uc['unread_count']
        c['last_message_ref'] = c.get('last_message', None)
        c['last_read_message_ref'] = uc.get('last_read_message', None)
        c['last_message'] = None
        c['last_read_message'] = None
        return Conversation.from_record(c)

    @classmethod
    def fetch_all_with_paging(cls, page, page_size, order='desc'):
        ucs = UserConversation.fetch_all_with_paging(page, page_size, order)
        result = [cls.__uc_to_conversation(uc)
                  for uc in ucs]
        result = [c for c in result if c is not None]
        participants, admins = cls.__get_participants_and_admins(result)
        for row in result:
            key = row.id.key
            row['admin_ids'] = admins[key]
            row['participant_ids'] = participants[key]
        return result

    @classmethod
    def fetch_one(cls, conversation_id, with_uc=True):
        result = None
        if with_uc:
            uc = UserConversation.fetch_one(conversation_id)
            if uc:
                result = cls.__uc_to_conversation(uc)
        else:
            if result is None:
                result = super(Conversation, cls).fetch_one(conversation_id)

        if result is None:
            msg = "Conversation not found,conversation_id=%s" %\
                  (conversation_id)
            raise SkygearChatException(msg)

        participants, admins = cls.__get_participants_and_admins([result])
        key = result.id.key
        result['admin_ids'] = admins[key]
        result['participant_ids'] = participants[key]
        return result

    @classmethod
    def __get_participants_and_admins(cls, conversations):
        database = cls._get_database()
        conversation_ids = [c.id.key for c in conversations]

        admins = {}
        participants = {}
        for key in conversation_ids:
            admins[key] = []
            participants[key] = []
        predicate = Predicate(conversation__in=list(set(conversation_ids)))
        query_result = database.query(
                       Query(UserConversation.record_type, predicate=predicate,
                             limit=None)
                       )
        for row in query_result:
            conversation_id = row['conversation'].recordID.key
            if row['is_admin']:
                admins[conversation_id].append(row['user'].recordID.key)
            participants[conversation_id].append(row['user'].recordID.key)

        return participants, admins

    @classmethod
    def get_message_acl(cls, conversation_id):
        return [RoleAccessControlEntry(
                cls.get_participant_role(conversation_id),
                ACCESS_CONTROL_ENTRY_LEVEL_WRITE)]

    @classmethod
    def exists(cls, conversation_id):
        conversation = Conversation.fetch_one(conversation_id)
        return not (conversation is None)
