import skygear

from skygear.utils.context import current_user_id

from .pubsub import _publish_event
from .exc import SkygearChatException


@skygear.before_save("conversation", async=False)
def handle_conversation_before_save(record, original_record, conn):
    if len(record.get('participant_ids', [])) == 0:
        raise SkygearChatException("no participants")

    if len(record['admin_ids']) == 0 \
            and not record.get('is_direct_message'):
        raise SkygearChatException("no admin assigned")

    if original_record is not None:
        if current_user_id() not in original_record.get('admin_ids', []):
            raise SkygearChatException("no permission to edit conversation")

    if original_record is None and record.get('is_direct_message'):
        if current_user_id() not in record['participant_ids']:
            raise SkygearChatException(
                "cannot create direct conversations for other users")

        if len(record['participant_ids']) != 2:
            raise SkygearChatException(
                "direct message must only have two participants")

        record['admin_ids'] = record['participant_ids']


@skygear.after_save("conversation")
def handle_conversation_after_save(record, original_record, conn):
    if original_record is None:
        for p_id in record['participant_ids']:
            _publish_event(
                p_id, "conversation", "create",
                record, original_record)

    else:
        p_ids = record['participant_ids'] + original_record['participant_ids']
        for p_id in set(p_ids):
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

