# Copyright 2017 Oursky Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from skygear.encoding import serialize_record

from .database import Database
from .decorators import (AFTER_CONVERSATION_CREATED_HOOK,
                         AFTER_CONVERSATION_DELETED_HOOK,
                         AFTER_CONVERSATION_UPDATED_HOOK,
                         AFTER_MESSAGE_DELETED_HOOK, AFTER_MESSAGE_SENT_HOOK,
                         AFTER_MESSAGE_UPDATED_HOOK,
                         AFTER_USERS_ADDED_TO_CONVERSATION_HOOK,
                         AFTER_USERS_REMOVED_FROM_CONVERSATION_HOOK,
                         TYPING_STARTED_HOOK)
from .predicate import Predicate
from .query import Query
from .utils import _get_container


def __send_hook(name, params):
    container = _get_container()
    container.send_action(name, {'args': params})


def __get_users_by_user_ids(user_ids):
    container = _get_container()
    database = Database(container, '')
    predicate = Predicate(_id__in=user_ids)
    query = Query('user', predicate=predicate, limit=10000)
    users = database.query(query)
    return [serialize_record(u) for u in users]


def send_after_message_sent_hook(message, conversation, participant_ids):
    participants = __get_users_by_user_ids(participant_ids)
    __send_hook(AFTER_MESSAGE_SENT_HOOK, {'message': message,
                                          'conversation': conversation,
                                          'participants': participants})


def send_after_message_updated_hook(message, conversation, participant_ids):
    participants = __get_users_by_user_ids(participant_ids)
    __send_hook(AFTER_MESSAGE_UPDATED_HOOK, {'message': message,
                                             'conversation': conversation,
                                             'participants': participants})


def send_after_message_deleted_hook(message, conversation, participant_ids):
    participants = __get_users_by_user_ids(participant_ids)
    __send_hook(AFTER_MESSAGE_DELETED_HOOK, {'message': message,
                                             'conversation': conversation,
                                             'participants': participants})


def send_typing_started_hook(conversation, participant_ids, events):
    participants = __get_users_by_user_ids(participant_ids)
    __send_hook(TYPING_STARTED_HOOK, {'conversation': conversation,
                                      'participants': participants,
                                      'events': events})


def send_after_conversation_created_hook(conversation, participant_ids):
    participants = __get_users_by_user_ids(participant_ids)
    data = {'conversation': conversation, 'participants': participants}
    __send_hook(AFTER_CONVERSATION_CREATED_HOOK, data)


def send_after_conversation_updated_hook(conversation, participant_ids):
    participants = __get_users_by_user_ids(participant_ids)
    data = {'conversation': conversation, 'participants': participants}
    __send_hook(AFTER_CONVERSATION_UPDATED_HOOK, data)


def send_after_conversation_deleted_hook(conversation, participant_ids):
    participants = __get_users_by_user_ids(participant_ids)
    data = {'conversation': conversation, 'participants': participants}
    __send_hook(AFTER_CONVERSATION_DELETED_HOOK, data)


def send_after_users_added_to_conversation_hook(conversation,
                                                participant_ids,
                                                new_user_ids):

    participants = __get_users_by_user_ids(participant_ids)
    new_users = __get_users_by_user_ids(new_user_ids)
    data = {'conversation': conversation,
            'participants': participants,
            'new_users': new_users}
    __send_hook(AFTER_USERS_ADDED_TO_CONVERSATION_HOOK, data)


def send_after_users_removed_from_conversation_hook(conversation,
                                                    participant_ids,
                                                    old_user_ids):
    participants = __get_users_by_user_ids(participant_ids)
    old_users = __get_users_by_user_ids(old_user_ids)
    data = {'conversation': conversation,
            'participants': participants,
            'old_users': old_users}
    __send_hook(AFTER_USERS_REMOVED_FROM_CONVERSATION_HOOK, data)
