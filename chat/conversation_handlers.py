from uuid import uuid4

from psycopg2.extensions import AsIs

import skygear
from skygear.transmitter.encoding import serialize_record
from skygear.utils import db
from skygear.utils.context import current_user_id

from .conversation import Conversation
from .database import Database
from .exc import (NotInConversationException, NotSupportedException,
                  SkygearChatException)
from .message import Message
from .pubsub import _publish_record_event
from .roles import RolesHelper
from .user import User
from .user_conversation import UserConversation
from .utils import (_get_container, _get_schema_name,
                    current_context_has_master_key)


def __validate_user_is_admin(conversation_id):
    uc = UserConversation.fetch_one(conversation_id)
    if uc is None or not uc['is_admin']:
        raise NotInConversationException()


def __validate_conversation(participants):
    valid = True
    with db.conn() as conn:
        result = conn.execute("""
                              SELECT 1 FROM
                                %(schema_name)s.conversation AS c
                                WHERE
                                    c.distinct_by_participants = TRUE
                                AND
                                (
                                    SELECT COUNT(DISTINCT user)
                                    FROM %(schema_name)s.user_conversation
                                    AS uc
                                    WHERE
                                        uc.conversation = c._id
                                    AND
                                        uc.user IN %(user_ids)s
                                ) = %(count)s
                              """, {'schema_name': AsIs(_get_schema_name()),
                                    'user_ids': tuple(participants),
                                    'count': len(participants)})

        valid = result.first() is None
    if not valid:
        raise SkygearChatException(
            "Conversation with the participants already exists")


def __update_roles(container, users, role, flag):
    roles_helper = RolesHelper(container)
    roles_helper.set_roles(users, [role], flag)


def __update_participant_roles(container, conversation_id, users, flag):
    __update_roles(container,
                   users,
                   Conversation.get_participant_role(conversation_id),
                   flag)


def __update_admin_roles(container, conversation_id, users, flag):
    __update_roles(container,
                   users,
                   Conversation.get_admin_role(conversation_id),
                   flag)


def __update_admin_flags(container, conversation_id, user_ids, flag):
    for user_id in user_ids:
        uc = UserConversation.fetch_one(conversation_id, user_id=user_id)
        if uc is None:
            c = Conversation.new(conversation_id, user_id)
            uc = UserConversation.new(c, user_id)
        uc.mark_admin(flag)


def __mark_conversation_non_distinct(database, conversation_id):
    database.save([{'_id': 'conversation/' + conversation_id,
                    'distinct_by_participants': False}])


def notify_users(record,
                 unchanged_participants,
                 old_participants,
                 new_participants):

    for each_user in unchanged_participants:
        _publish_record_event(each_user,
                              "conversation",
                              "update",
                              record)

    for each_user in old_participants:
        _publish_record_event(each_user,
                              "conversation",
                              "delete",
                              record)

    for each_user in new_participants:
        _publish_record_event(each_user,
                              "conversation",
                              "create",
                              record)


def handle_conversation_before_delete(record, conn):
    raise NotSupportedException("Deleting a conversation is not supported")


def handle_leave_conversation(conversation_id):
    uc = UserConversation.fetch_one(conversation_id)
    if uc is None:
        raise NotInConversationException()
    uc.delete()
    return {'status': 'OK'}


def handle_add_participants(conversation_id,
                            participant_ids,
                            is_first_time=False):

    existing_participants = []
    for participant in participant_ids:
        uc = UserConversation.fetch_one(conversation_id,
                                        user_id=participant)
        if uc is not None:
            existing_participants.append(participant)

    participant_ids = [x for x in participant_ids
                       if x not in existing_participants]

    container = _get_container()
    __update_participant_roles(container,
                               conversation_id,
                               participant_ids, True)

    conversation = Conversation.new(conversation_id, current_user_id())
    for participant_id in participant_ids:
        UserConversation.new(conversation, participant_id).save()

    if not is_first_time:
        database = Database(container, '_public')
        __mark_conversation_non_distinct(database, conversation_id)

    conversation = Conversation.fetch_one(conversation_id)
    existing_participants = conversation['participant_ids']
    notify_users(conversation,
                 existing_participants,
                 [],
                 participant_ids)
    return {'conversation': serialize_record(conversation)}


def handle_remove_participants(conversation_id, participant_ids):
    container = _get_container()
    __update_participant_roles(container,
                               conversation_id,
                               participant_ids,
                               False)
    database = Database(container, '_public')
    conversation = Conversation.new(conversation_id, current_user_id())
    ucs = [UserConversation.new(conversation, participant_id)
           for participant_id in participant_ids]
    UserConversation.delete_all(ucs)
    __mark_conversation_non_distinct(database, conversation_id)

    conversation = Conversation.fetch_one(conversation_id)
    notify_users(conversation,
                 conversation['participant_ids'],
                 participant_ids,
                 [])
    return {'conversation': serialize_record(conversation)}


def handle_admins_lambda(conversation_id, admin_ids, flag):
    container = _get_container()
    __update_admin_roles(container, conversation_id, admin_ids, flag)
    __update_admin_flags(container, conversation_id, admin_ids, flag)
    r = Conversation.fetch_one(conversation_id)
    return {'conversation': serialize_record(r)}


def check_if_context_has_master_key(msg):
    if not current_context_has_master_key():
        raise NotSupportedException(msg)


def register_conversation_hooks(settings):
    @skygear.before_save("conversation", async=False)
    def conversation_before_save_handler(record, original_record, conn):
        if original_record is None:
            check_if_context_has_master_key(
                    "Call chat:create_conversation instead")
        if 'admin_ids' in record:
            del record['admin_ids']
        if 'participant_ids' in record:
            del record['participant_ids']

    @skygear.before_delete("conversation", async=False)
    def conversation_before_delete_handler(record, conn):
        check_if_context_has_master_key(
                "Deleting a conversation is not supported")


def __get_messsage_refs_from_conversation(conversation):
    refs = []
    last_message_ref = conversation.get('last_message_ref', None)
    if last_message_ref is not None:
        refs.append(last_message_ref)
    last_read_message_ref = conversation.get('last_read_message_ref', None)
    if last_read_message_ref is not None:
        refs.append(last_read_message_ref)
    return refs


def __update_conversation_messages(conversation, messages):
    last_message_ref = conversation.get('last_message_ref')
    last_read_message_ref = conversation.get('last_read_message_ref')

    if last_message_ref is not None:
        key = last_message_ref.recordID.key
        conversation['last_message'] = messages[key]

    if last_read_message_ref is not None:
        key = last_read_message_ref.recordID.key
        conversation['last_read_message'] = messages[key]
    return conversation


def handle_get_conversation_lambda(conversation_id, include_last_message):
    conversation = Conversation.fetch_one(conversation_id)
    if conversation is None:
        raise SkygearChatException("Conversation not found.")

    if None and include_last_message:
        message_refs = __get_messsage_refs_from_conversation(conversation)
        messages = Message.fetch_all(message_refs)
        messages = {message.id.key: serialize_record(message)
                    for message in messages}
        conversation = __update_conversation_messages(conversation, messages)

    return {'conversation': serialize_record(conversation)}


def handle_get_conversations_lambda(page, page_size, include_last_message):
    result = Conversation.fetch_all_with_paging(page, page_size)
    if include_last_message:
        messages = {}
        message_refs = []
        for conversation in result:
            message_refs = message_refs +\
                __get_messsage_refs_from_conversation(conversation)

        messages = Message.fetch_all(message_refs)
        messages = {message.id.key: serialize_record(message)
                    for message in messages}
        n = len(result)
        for i in range(0, n):
            result[i] = __update_conversation_messages(
                        result[i], messages)

    return {"conversations": [serialize_record(r) for r in result]}


def handle_delete_conversation_lambda(conversation_id):
    # TODO: implement deletion, kick all participants and admin
    return None


def handle_create_conversation_lambda(participants, title, meta, options):
    participants = [p if isinstance(p, str) else
                    User.deserialize(p).id.key for p in participants]
    if options is None:
        options = {}
    user_id = current_user_id()
    admins = [user_id]
    admins_from_options = [User.deserialize(a).id.key
                           for a in options.get('admin_ids', [])]
    admins = list(set(admins + admins_from_options))
    participants = list(set(participants + admins))

    is_distinct = options.get('distinctByParticipants', False)
    if is_distinct:
        __validate_conversation(participants)

    conversation_id = str(uuid4())
    conversation = Conversation.new(conversation_id, user_id)
    conversation['title'] = title
    conversation['distinct_by_participants'] = is_distinct
    conversation['meta'] = meta
    conversation.save()
    conversation['admin_ids'] = []
    conversation['participant_ids'] = []
    handle_add_participants(conversation_id, participants, True)
    handle_admins_lambda(conversation_id, admins, True)
    conversation['admin_ids'] = admins
    conversation['participant_ids'] = list(set(participants + admins))
    return {'conversation': serialize_record(conversation)}


def register_conversation_lambdas(settings):
    @skygear.op("chat:leave_conversation",
                auth_required=True, user_required=True)
    def leave_conversation_lambda(conversation_id):
        return handle_leave_conversation(conversation_id)

    @skygear.op("chat:add_participants",
                auth_required=True, user_required=True)
    def add_participants_lambda(conversation_id, participants):
        __validate_user_is_admin(conversation_id)
        return handle_add_participants(conversation_id, participants)

    @skygear.op("chat:remove_participants",
                auth_required=True, user_required=True)
    def remove_participants_lambda(conversation_id, participants):
        __validate_user_is_admin(conversation_id)
        return handle_remove_participants(conversation_id, participants)

    @skygear.op("chat:add_admins",
                auth_required=True, user_required=True)
    def add_admins_lambda(conversation_id, admins):
        __validate_user_is_admin(conversation_id)
        return handle_admins_lambda(conversation_id, admins, True)

    @skygear.op("chat:remove_admins",
                auth_required=True, user_required=True)
    def remove_admins_lambda(conversation_id, admins):
        __validate_user_is_admin(conversation_id)
        return handle_admins_lambda(conversation_id, admins, False)

    @skygear.op("chat:get_conversations",
                auth_required=True, user_required=True)
    def get_conversations_lambda(page, page_size, include_last_message):
        return handle_get_conversations_lambda(page,
                                               page_size,
                                               include_last_message)

    @skygear.op("chat:get_conversation",
                auth_required=True, user_required=True)
    def get_conversation_lambda(conversation_id, include_last_message):
        return handle_get_conversation_lambda(conversation_id,
                                              include_last_message)

    @skygear.op("chat:create_conversation",
                auth_required=True, user_required=True)
    def create_conversation_lambda(participants, title, meta, options):
        return handle_create_conversation_lambda(participants,
                                                 title,
                                                 meta,
                                                 options)

    @skygear.op("chat:delete_conversation",
                auth_required=True, user_required=True)
    def delete_conversation_lambda(conversation_id):
        return handle_delete_conversation_lambda(conversation_id)
