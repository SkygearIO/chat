import skygear
from skygear.container import SkygearContainer
from skygear.models import DirectAccessControlEntry, PublicAccessControlEntry
from skygear.skyconfig import config as skygear_config
from skygear.utils.context import current_user_id

from .exc import SkygearChatException
from .pubsub import _publish_record_event
from .user_conversation import UserConversation


class Conversation():
    def __init__(self, record, master_key=None):
        if record is None:
            raise Exception('Cannot create conversation without record')

        self.master_key = master_key
        if self.master_key is None:
            self.master_key = skygear_config.app.master_key

        self.record = record

    def __len__(self):
        return len(self.record)

    def __getitem__(self, key):
        return self.record[key]

    def __setitem__(self, key, value):
        self.record[key] = value

    def __delitem__(self, key):
        del self.record[key]

    def __iter__(self):
        return iter(self.record)

    def __contains__(self, item):
        return item in self.record

    def get(self, key, default=None):
        return self.record.get(key, default)

    def preprocess(self):
        if len(self.get('admin_ids', [])) == 0:
            self['admin_ids'] = self['participant_ids']

        self['participant_count'] = len(self['participant_ids'])

        acl = [PublicAccessControlEntry('read')]
        for admin_id in self['admin_ids']:
            acl.append(DirectAccessControlEntry(admin_id, 'write'))
        self.record._acl = acl

    def validate(self):
        if len(self.get('participant_ids', [])) == 0:
            raise SkygearChatException("Conversation must have participants")
        if not set(self['participant_ids']) >= set(self['admin_ids']):
            raise SkygearChatException("Admins should also be participants")
        for user_id in self['participant_ids']:
            if user_id.startswith('user/'):
                raise SkygearChatException(
                    "Some participant IDs are not in correct format")
        self.check_distinct_by_participants()

    def check_distinct_by_participants(self):
        if self.get('distinct_by_participants', False):
            participant_ids = self['participant_ids']
            predicate = [
                'and',
                [
                    'eq',
                    {'$type': 'keypath', '$val': 'distinct_by_participants'},
                    True
                ],
                [
                    'eq',
                    {'$type': 'keypath', '$val': 'participant_count'},
                    len(participant_ids)
                ],
                [
                    'neq',
                    {'$type': 'keypath', '$val': '_id'},
                    self.record.id.key
                ]
            ]
            for each_participant_id in self['participant_ids']:
                predicate.append([
                    'in',
                    each_participant_id,
                    {'$type': 'keypath', '$val': 'participant_ids'}
                ])
            container = SkygearContainer(api_key=self.master_key)
            resp = container.send_action('record:query', {
                'database_id': '_public',
                'limit': 1,
                'record_type': 'conversation',
                'predicate': predicate
            })
            if len(resp['result']) != 0:
                raise SkygearChatException(
                    "Conversation with the participants already exists")

    def get_participant_set(self):
        return set(self.get('participant_ids'))

    def get_admin_set(self):
        return set(self.get('admin_ids'))


class ConversationChangeOperation():
    def __init__(self, old_conversation_record, new_conversation_record):
        if old_conversation_record is not None:
            self.old_conversation = Conversation(old_conversation_record)
            self.is_new = False
        else:
            self.old_conversation = None
            self.is_new = True
        self.new_conversation = Conversation(new_conversation_record)

    def validate(self):
        user_id = current_user_id()
        if self.is_new:
            if user_id not in self.new_conversation['participant_ids']:
                raise SkygearChatException(
                    "Cannot create conversations for other users")
        else:
            if user_id not in self.old_conversation.get('admin_ids', []):
                raise SkygearChatException(
                    "no permission to edit conversation")

    def update_user_conversations(self):
        old_participants = set()
        if self.old_conversation is not None:
            old_participants = self.old_conversation.get_participant_set()
        new_participants = self.new_conversation.get_participant_set()

        participants_to_delete = old_participants - new_participants
        for each_participant_id in participants_to_delete:
            each_participant = UserConversation(
                self.new_conversation,
                each_participant_id
            )
            each_participant.delete()

        participants_to_create = new_participants - old_participants
        for each_participant_id in participants_to_create:
            each_participant = UserConversation(
                self.new_conversation,
                each_participant_id
            )
            each_participant.create()

    def notify_users(self):
        users_to_publish = self.new_conversation.get_participant_set()
        new_record = self.new_conversation.record
        old_record = None
        if self.old_conversation is not None:
            old_participants = self.old_conversation.get_participant_set()
            users_to_publish = users_to_publish | old_participants
            old_record = self.old_conversation.record
        for each_user in users_to_publish:
            _publish_record_event(
                each_user, "conversation", "update", new_record, old_record)


def handle_conversation_before_save(record, original_record, conn):
    changes = ConversationChangeOperation(original_record, record)
    changes.new_conversation.validate()
    changes.new_conversation.preprocess()
    changes.validate()


def handle_conversation_after_save(record, original_record, conn):
    changes = ConversationChangeOperation(original_record, record)
    changes.update_user_conversations()


def pubsub_conversation_after_save(record, original_record, conn):
    changes = ConversationChangeOperation(original_record, record)
    changes.notify_users()


def handle_conversation_before_delete(record, conn):
    conversation = Conversation(record)
    if current_user_id() not in conversation.get_admin_set():
        raise SkygearChatException("no permission to delete conversation")


def handle_conversation_after_delete(record, conn):
    conversation = Conversation(record)
    for each_participant in conversation.get_participant_set():
        _publish_record_event(
            each_participant, "conversation", "delete", conversation.record)


def register_conversation_hooks(settings):
    @skygear.before_save("conversation", async=False)
    def conversation_before_save_handler(record, original_record, conn):
        return handle_conversation_before_save(record, original_record, conn)

    @skygear.after_save("conversation", async=False)
    def conversation_after_save_handler(record, original_record, conn):
        return handle_conversation_after_save(record, original_record, conn)

    @skygear.after_save("conversation")
    def conversation_after_save_pubsub_handler(record, original_record, conn):
        return pubsub_conversation_after_save(record, original_record, conn)

    @skygear.before_delete("conversation", async=False)
    def conversation_before_delete_handler(record, conn):
        return handle_conversation_before_delete(record, conn)

    @skygear.after_delete("conversation")
    def conversation_after_delete_handler(record, conn):
        return handle_conversation_after_delete(record, conn)
