from uuid import uuid4

from psycopg2.extensions import AsIs

import skygear
from skygear.transmitter.encoding import _RecordDecoder, deserialize_record
from skygear.utils import db
from skygear.utils.context import current_user_id

from .conversation import Conversation, get_admin_role, get_participant_role
from .database import Database
from .exc import (NotInConversationException, NotSupportedException,
                  SkygearChatException)
from .predicate import Predicate
from .pubsub import _publish_record_event
from .query import Query
from .roles import RolesHelper
from .user import User
from .user_conversation import UserConversation, is_user_id_in_conversation
from .utils import (_get_container, _get_conversation, _get_schema_name,
                    current_context_has_master_key,
                    get_participants_and_admins)


def __validate_user_is_admin(conversation_id):
    if not is_user_id_in_conversation(current_user_id(),
                                      conversation_id,
                                      True):
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
                   get_participant_role(conversation_id),
                   flag)


def __update_admin_roles(container, conversation_id, users, flag):
    __update_roles(container, users, get_admin_role(conversation_id), flag)


def __update_admin_flags(container, conversation, users, flag):
    records = [{'_id': 'user_conversation/' + UserConversation.
                get_consistent_hash(conversation, user),
                'is_admin': flag} for user in users]
    database = Database(container, '_public')
    database.save(records)


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
    if not is_user_id_in_conversation(current_user_id(),
                                      is_user_id_in_conversation):
        raise NotInConversationException()
    uc = UserConversation(conversation_id, current_user_id())
    uc.delete()
    return {'status': 'OK'}


def handle_add_participants(conversation_id,
                            participants,
                            is_first_time=False):

    r = _get_conversation(conversation_id)
    container = _get_container()

    __update_participant_roles(container, conversation_id, participants, True)
    database = Database(container, '_public')
    database.save([UserConversation(conversation_id, participant)
                   for participant in participants])
    r = _get_conversation(conversation_id)
    if not is_first_time:
        __mark_conversation_non_distinct(database, conversation_id)

    existing_participants = []
    notify_users(deserialize_record(r),
                 existing_participants,
                 [],
                 participants)
    return {'conversation': r}


def handle_remove_participants(conversation_id, participants):
    container = _get_container()
    __update_participant_roles(container, conversation_id, participants, False)
    database = Database(container, '_public')
    database.delete([UserConversation(conversation_id, participant)
                    for participant in participants])
    __mark_conversation_non_distinct(database, conversation_id)
    r = _get_conversation(conversation_id)
    notify_users(deserialize_record(r), r['participant_ids'], participants, [])
    return {'conversation': r}


def handle_admins_lambda(conversation_id, admins, flag):
    container = _get_container()
    __update_admin_roles(container, conversation_id, admins, flag)
    __update_admin_flags(container, conversation_id, admins, flag)
    r = _get_conversation(conversation_id)
    return {'conversation': r}


def check_if_context_has_master_key(msg):
    if not current_context_has_master_key():
        raise NotSupportedException(msg)


def register_conversation_hooks(settings):
    @skygear.before_save("conversation", async=False)
    def conversation_before_save_handler(record, original_record, conn):
        if original_record is None:
            check_if_context_has_master_key(
                    "Call chat:create_conversation instead")

    @skygear.before_delete("conversation", async=False)
    def conversation_before_delete_handler(record, conn):
        check_if_context_has_master_key(
                "Deleting a conversation is not supported")


def __uc_to_conversation(uc):
    d = {}
    d.update(uc["_transient"]["conversation"])
    d['unread_count'] = uc['unread_count']
    d['last_message_ref'] = d.get('last_message', None)
    d['last_read_message_ref'] = uc.get('last_read_message', None)
    d['last_message'] = None
    d['last_read_mesage'] = None
    return d


def __get_messsage_ids_from_conversation(conversation):
    ids = []
    decoder = _RecordDecoder()
    last_message_ref = conversation.get('last_message_ref', None)
    if last_message_ref is not None:
        ids.append(decoder.decode_ref(last_message_ref).recordID.key)
    last_read_message_ref = conversation.get('last_read_message_ref', None)
    if last_read_message_ref is not None:
        ids.append(decoder.decode_ref(last_read_message_ref).recordID.key)
    return ids


def __get_messages_by_ids(database, message_ids):
    decoder = _RecordDecoder()
    messages = {}
    message_predicate = Predicate(_id__in=message_ids, deleted__eq=False)
    message_query = Query('message', predicate=message_predicate)
    message_result = database.query(message_query)["result"]
    for row in message_result:
        key = decoder.decode_id(row['_id']).key
        messages[key] = row
    return messages


def __update_conversation_messages(conversation, messages):
    decoder = _RecordDecoder()
    last_message_ref = conversation.get('last_message_ref')
    last_read_message_ref = conversation.get('last_read_message_ref')

    if last_message_ref is not None:
        key = decoder.decode_ref(last_message_ref).recordID.key
        conversation['last_message'] = messages[key]

    if last_read_message_ref is not None:
        key = decoder.decode_ref(last_read_message_ref).recordID.key
        conversation['last_read_message'] = messages[key]
    return conversation


def handle_get_conversation_lambda(conversation_id, include_last_message):
    container = _get_container()
    database = Database(container, '_public')
    query_result = database.query(
                   Query('user_conversation',
                         predicate=Predicate(user__eq=current_user_id(),
                                             conversation__eq=conversation_id),
                         limit=1,
                         include=["conversation", "user"]))["result"]
    conversation = None
    if len(query_result) == 1:
        conversation = __uc_to_conversation(query_result[0])

    if conversation is not None and include_last_message:
        message_ids = __get_messsage_ids_from_conversation(conversation)
        messages = __get_messages_by_ids(database, message_ids)
        conversation = __update_conversation_messages(conversation, messages)
    return {'conversation': conversation}


def handle_get_conversations_lambda(page, page_size, include_last_message):
    container = _get_container()
    database = Database(container, '_public')
    offset = (page - 1) * page_size
    query_result = database.query(
                   Query('user_conversation',
                         predicate=Predicate(user__eq=current_user_id()),
                         offset=offset,
                         limit=page_size,
                         include=["conversation", "user"]))["result"]
    result = []
    decoder = _RecordDecoder()
    conversation_ids = []
    message_ids = []
    for row in query_result:
        conversation = __uc_to_conversation(row)
        conversation_ids.append(decoder.decode_id(conversation['_id']).key)
        message_ids = message_ids +\
            __get_messsage_ids_from_conversation(conversation)
        result.append(conversation)

    messages = {}
    if include_last_message:
        messages = __get_messages_by_ids(database, message_ids)

    participants, admins = get_participants_and_admins(conversation_ids)
    for row in result:
        conversation = decoder.decode_id(row['_id']).key
        row['admin_ids'] = admins[conversation]
        row['participant_ids'] = participants[conversation]
        if include_last_message:
            row = __update_conversation_messages(row, messages)

    return {"result": result}


def handle_delete_conversation_lambda(conversation_id):
    # TODO: implement deletion, kick all participants and admin
    return None


def handle_create_conversation_lambda(participants, title, meta, options):
    participants = [User.deserialize(p).id.key for p in participants]
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
    conversation = Conversation(conversation_id, user_id)
    conversation['title'] = title
    conversation['distinct_by_participants'] = is_distinct
    conversation['meta'] = meta

    container = _get_container()
    database = Database(container, '_public')
    result = database.save(conversation)
    handle_add_participants(conversation_id, participants, True)
    handle_admins_lambda(conversation_id, admins, True)
    return result


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
