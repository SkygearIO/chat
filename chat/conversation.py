import skygear
from skygear.container import SkygearContainer
from skygear.models import DirectAccessControlEntry, PublicAccessControlEntry
from skygear.options import options as skyoptions
from skygear.utils.context import current_user_id

from .exc import (InvalidArgumentException, NotInConversationException,
                  NotSupportedException, SkygearChatException)
from .pubsub import _publish_record_event
from .user_conversation import UserConversation
from .utils import _get_conversation, current_context_has_master_key


class Conversation():
    def __init__(self, record, master_key=None):
        if record is None:
            raise Exception('Cannot create conversation without record')

        self.master_key = master_key
        if self.master_key is None:
            self.master_key = skyoptions.masterkey

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
        if not set(self['participant_ids']) >= set(self['admin_ids']):
            raise InvalidArgumentException(
                "Admins should also be participants",
                ['participant_ids']
            )
        for user_id in self['participant_ids']:
            if user_id.startswith('user/'):
                raise InvalidArgumentException(
                    "Some participant IDs are not in correct format",
                    ['participant_ids'])
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

    @property
    def participant_set(self):
        return set(self.get('participant_ids'))

    @participant_set.setter
    def participant_set(self, participant_set):
        self.record['participant_ids'] = list(participant_set)

    @property
    def admin_set(self):
        return set(self.get('admin_ids'))

    @admin_set.setter
    def admin_set(self, admin_set):
        self.record['admin_ids'] = list(admin_set)

    def is_participant(self, user_id: str) -> bool:
        """
        Returns whether the user is a participant in the conversation.
        """
        return user_id in self.get('participant_ids')

    def save(self):
        container = SkygearContainer(api_key=self.master_key,
                                     user_id=current_user_id())
        return container.send_action('record:save', {
            'database_id': '_public',
            'records': [self.record]
        })


class ConversationChangeOperation():
    def __init__(self, old_conversation_record, new_conversation_record):
        if old_conversation_record is not None:
            self.old_conversation = Conversation(old_conversation_record)
            self.is_new = False
        else:
            self.old_conversation = None
            self.is_new = True
        self.new_conversation = Conversation(new_conversation_record)

    @property
    def new_participants(self):
        return self.new_conversation.participant_set

    @property
    def old_participants(self):
        old_participants = set()
        if self.old_conversation is not None:
            old_participants = self.old_conversation.participant_set
        return old_participants

    @property
    def participants_to_create(self):
        return self.new_participants - self.old_participants

    @property
    def participants_to_delete(self):
        return self.old_participants - self.new_participants

    def validate(self):
        user_id = current_user_id()
        if self.is_new:
            participants = self.new_conversation.participant_set
            if len(participants) == 0:
                raise SkygearChatException(
                   "Conversation must have participants")
            if user_id not in participants:
                raise SkygearChatException(
                    "Cannot create conversations for other users")
        else:
            if current_context_has_master_key():
                # do nothing, having master key can override checks here
                pass
            elif user_id not in self.old_conversation.get('admin_ids', []):
                raise SkygearChatException(
                    "no permission to edit conversation")

    def update_user_conversations(self):
        for each_participant_id in self.participants_to_delete:
            each_participant = UserConversation(
                self.new_conversation,
                each_participant_id
            )
            each_participant.delete()

        for each_participant_id in self.participants_to_create:
            each_participant = UserConversation(
                self.new_conversation,
                each_participant_id
            )
            each_participant.create()

    def notify_users(self):
        new_record = self.new_conversation.record

        unchange_participants = self.new_participants & self.old_participants
        for each_user in unchange_participants:
            _publish_record_event(
                each_user, "conversation", "update", new_record)

        if self.old_conversation:
            old_record = self.old_conversation.record
            for each_user in self.participants_to_delete:
                _publish_record_event(
                    each_user, "conversation", "delete", old_record)

        for each_user in self.participants_to_create:
            _publish_record_event(
                each_user, "conversation", "create", new_record)


def handle_conversation_before_save(record, original_record, conn):
    changes = ConversationChangeOperation(original_record, record)
    changes.new_conversation.preprocess()
    changes.new_conversation.validate()
    changes.validate()


def handle_conversation_after_save(record, original_record, conn):
    changes = ConversationChangeOperation(original_record, record)
    changes.update_user_conversations()


def pubsub_conversation_after_save(record, original_record, conn):
    changes = ConversationChangeOperation(original_record, record)
    changes.notify_users()


def handle_conversation_before_delete(record, conn):
    raise NotSupportedException("Deleting a conversation is not supported")


def handle_leave_conversation(conversation_id):
    conversation = Conversation(_get_conversation(conversation_id))
    if not conversation.is_participant(current_user_id()):
        raise NotInConversationException()

    # Remove the current user from the participant and the admin list (if
    # exists in the list). Save the conversation using master key
    # so that the conversation without the user being in the admin list.
    conversation.participant_set -= set([current_user_id()])
    conversation.admin_set -= set([current_user_id()])
    conversation.save()
    return {'status': 'OK'}


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


def register_conversation_lambdas(settings):
    @skygear.op("chat:leave_conversation",
                auth_required=True, user_required=True)
    def leave_conversation_lambda(conversation_id):
        return handle_leave_conversation(conversation_id)
