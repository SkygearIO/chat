import skygear
from skygear.container import SkygearContainer
from skygear.utils.context import current_user_id


container = SkygearContainer()
container.api_key = "my_skygear_key"
container.app_name = "my_skygear_app"


@skygear.before_save("conversation", async=False)
def handle_conversation_before_save(new_record, old_record, db):
    # TODO: check user exists

    if len(new_record['participant_ids']) == 0:
        raise Exception("no participants")

    if len(new_record['admin_ids']) == 0:
        raise Exception("no admin assigned")

    if old_record is not None:
        if current_user_id() not in old_record['admin_ids']:
            raise Exception("no permission to edit conversation")


@skygear.before_delete("conversation", async=False)
def handle_conversation_before_delete(record, db):
    if current_user_id() not in record['admin_ids']:
        raise Exception("no permission to delete conversation")
