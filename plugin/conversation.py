import skygear
from skygear.models import DirectAccessControlEntry, PublicAccessControlEntry
from skygear.utils.context import current_user_id

from .exc import SkygearChatException
from .pubsub import _publish_event
from .user_conversation import UserConversation


@skygear.before_save("conversation", async=False)
def handle_conversation_before_save(record, original_record, conn):
    validate_conversation(record)
    if record.get('is_direct_message'):
        record['admin_ids'] = record['participant_ids']
    if len(record.get('admin_ids', [])) == 0:
        record['admin_ids'] = record['participant_ids']

    is_new = original_record is None
    # Check permission
    if not is_new:
        if current_user_id() not in original_record.get('admin_ids', []):
            raise SkygearChatException("no permission to edit conversation")
    else:
        if current_user_id() not in record['participant_ids']:
            raise SkygearChatException(
                "cannot create conversations for other users")

    # Set the correct ACL at server side
    record._acl = [PublicAccessControlEntry('read')]
    for admin_id in record['admin_ids']:
        if admin_id in record['participant_ids']:
            record.acl.append(DirectAccessControlEntry(admin_id, 'write'))


def validate_conversation(record):
    if len(record.get('participant_ids', [])) == 0:
        raise SkygearChatException("converation must have participant")
    if record.get('is_direct_message'):
        if len(record['participant_ids']) != 2:
            raise SkygearChatException(
                "direct message must only have two participants")
    if not set(record['participant_ids']) >= set(record['admin_ids']):
        raise SkygearChatException(
            "admins should also be participants")

    for user_id in record.get('participant_ids', []):
        validate_user_id(user_id)
    for user_id in record.get('admin_ids', []):
        validate_user_id(user_id)


def validate_user_id(user_id):
    if user_id.startswith('user/'):
        raise SkygearChatException("user_id is not in correct format")


@skygear.after_save("conversation", async=False)
def handle_conversation_after_save(record, original_record, conn):
    if original_record is None:
        orig_participant = set()
    else:
        orig_participant = set(original_record['participant_ids'])
    participant = set(record['participant_ids'])

    # Create and remove
    uc = UserConversation(record.id)
    to_create = participant - orig_participant
    uc.create(to_create)
    to_delete = orig_participant - participant
    uc.delete(to_delete)


@skygear.after_save("conversation")
def pubsub_conversation_after_save(record, original_record, conn):
    p_ids = set(record['participant_ids'])
    if original_record is not None:
        orig_participant = set(original_record['participant_ids'])
        p_ids = p_ids | orig_participant

    # Notification
    for p_id in p_ids:
        _publish_event(
            p_id, "conversation", "update", record, original_record)


@skygear.before_delete("conversation", async=False)
def handle_conversation_before_delete(record, conn):
    if current_user_id() not in record['admin_ids']:
        raise SkygearChatException("no permission to delete conversation")


@skygear.after_delete("conversation")
def handle_conversation_after_delete(record, conn):
    for p_id in record['participant_ids']:
        _publish_event(
            p_id, "conversation", "delete", record)
