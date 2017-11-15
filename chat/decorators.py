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


from skygear import op

AFTER_MESSAGE_SENT_HOOK = "chat:after_message_sent_hook"
AFTER_MESSAGE_UPDATED_HOOK = "chat:after_message_updated_hook"
AFTER_MESSAGE_DELETED_HOOK = "chat:after_message_deleted_hook"
TYPING_STARTED_HOOK = "chat:typing_started_hook"
AFTER_CONVERSATION_CREATED_HOOK = "chat:after_conversation_created_hook"
AFTER_CONVERSATION_UPDATED_HOOK = "chat:after_conversation_updated_hook"
AFTER_CONVERSATION_DELETED_HOOK = "chat:after_conversation_deleted_hook"
AFTER_USERS_ADDED_TO_CONVERSATION_HOOK = \
    "chat:after_users_added_to_conversation_hook"
AFTER_USERS_REMOVED_FROM_CONVERSATION_HOOK = \
    "chat:after_users_removed_from_conversation_hook"

after_message_sent = op(AFTER_MESSAGE_SENT_HOOK,
                        auth_required=True,
                        user_required=True)
after_message_updated = op(AFTER_MESSAGE_UPDATED_HOOK,
                           auth_required=True,
                           user_required=True)
after_message_deleted = op(AFTER_MESSAGE_DELETED_HOOK,
                           auth_required=True,
                           user_required=True)
typing_started = op(TYPING_STARTED_HOOK,
                    auth_required=True,
                    user_required=True)
after_conversation_created = op(AFTER_CONVERSATION_CREATED_HOOK,
                                auth_required=True,
                                user_required=True)
after_conversation_updated = op(AFTER_CONVERSATION_UPDATED_HOOK,
                                auth_required=True,
                                user_required=True)
after_conversation_deleted = op(AFTER_CONVERSATION_DELETED_HOOK,
                                auth_required=True,
                                user_required=True)
after_users_added_to_conversation = op(AFTER_USERS_ADDED_TO_CONVERSATION_HOOK,
                                       auth_required=True,
                                       user_required=True)
after_users_removed_from_conversation = op(
    AFTER_USERS_REMOVED_FROM_CONVERSATION_HOOK,
    auth_required=True,
    user_required=True)
