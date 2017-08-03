import uuid

from skygear.models import RecordID, Reference
from skygear.utils.context import current_user_id

from .record import ChatRecord


class MessageHistory(ChatRecord):
    record_type = 'message_history'

    def __init__(self, message):
        super().__init__(RecordID(self.record_type, str(uuid.uuid4())),
                         current_user_id(),
                         message.acl)
        for key in ['attachment', 'body', 'metadata',
                    'conversation', 'message_status',
                    'edited_by', 'edited_at']:
            if key in message:
                self[key] = message.get(key, None)
        self['parent'] = Reference(message.id)
