import uuid

from skygear.container import SkygearContainer
from skygear.options import options as skyoptions
from skygear.transmitter.encoding import serialize_record
from skygear.utils.context import current_user_id


class MessageHistory:
    def __init__(self, message):
        message_record = serialize_record(message.record)
        self.record = {}
        for key in ['attachment', 'body', 'metadata',
                    'conversation', 'message_status']:
            if key in message_record:
                self.record[key] = message_record[key]
        self.record['parent'] = {'$type': 'ref',
                                 '$id': 'message/' + message.record.id._key}
        self.record['_id'] = 'message_history/' + str(uuid.uuid4())

    def save(self) -> None:
        """
        Save the Message History record to the database.
        """
        container = SkygearContainer(api_key=skyoptions.masterkey,
                                     user_id=current_user_id())
        container.send_action('record:save', {
            'database_id': '_public',
            'records': [self.record]
        })
