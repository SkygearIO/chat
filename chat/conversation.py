from skygear.models import (ACCESS_CONTROL_ENTRY_LEVEL_READ,
                            ACCESS_CONTROL_ENTRY_LEVEL_WRITE, Record, RecordID,
                            RoleAccessControlEntry)


class Conversation(Record):
    def __init__(self, conversation_id, user_id):
        super().__init__(RecordID('conversation', conversation_id),
                         user_id,
                         [RoleAccessControlEntry(
                          get_admin_role(conversation_id),
                          ACCESS_CONTROL_ENTRY_LEVEL_WRITE),
                          RoleAccessControlEntry(
                          get_participant_role(conversation_id),
                          ACCESS_CONTROL_ENTRY_LEVEL_READ)])


def get_participant_role(conversation_id):
    return "conversation-participant-%s" % (conversation_id)


def get_admin_role(conversation_id):
    return "conversation-admin-%s" % (conversation_id)


def get_message_acl(conversation_id):
    return [RoleAccessControlEntry(
            get_participant_role(conversation_id),
            ACCESS_CONTROL_ENTRY_LEVEL_WRITE)]
