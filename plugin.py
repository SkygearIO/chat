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

def _get_conversation(conversation_id):
    data = {
        'database_id': '_public',
        'record_type': 'conversation',
        'limit': 50,
        'sort': [],
        'include': {},
        'count': False,
        'predicate': [
        'eq', {
            '$type': 'keypath',
            '$val': '_id'
        },
        conversation_id]
    }

    response = skygear.container.send_action(
        container._request_url('record:query'),
        container._payload('record:query', data)
    )

    if len(response['result']) == 0:
        raise Exception("no conversation found")

    return response['result'][0]

@skygear.before_save("message", async=False)
def handle_message_before_save(new_record, old_record, db):
    conversation = _get_conversation(new_record['conversation_id'])

    if current_user_id() not in conversation['participant_ids']:
        raise Exception("user not in conversation")

    if old_record is not None:
        raise Exception("message is not editable")
