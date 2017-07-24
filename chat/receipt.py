import hashlib
import uuid
from datetime import datetime

from skygear.models import RecordID, Reference

from .record import ChatRecord


class Receipt(ChatRecord):
    record_type = 'receipt'
    DELIVERED_AT = 'delivered_at'
    READ_AT = 'read_at'

    @classmethod
    def new(cls, user_id: str, message_id: str):
        if not isinstance(user_id, str):
            raise ValueError('user_id is not str')
        if not isinstance(message_id, str):
            raise ValueError('message_id is not str')
        return cls(
            RecordID(cls.record_type,
                     Receipt.consistent_id(user_id, message_id)),
            user_id,
            None,
            data={
                'user': Reference(RecordID('user', user_id)),
                'message': Reference(RecordID('message', message_id))
            }
        )

    @classmethod
    def consistent_id(cls, user_id: str, message_id: str) -> str:
        seed = message_id + user_id
        sha = hashlib.sha256(bytes(seed, 'utf8'))
        return str(uuid.UUID(bytes=sha.digest()[0:16]))

    def mark_as_delivered(self) -> None:
        self[Receipt.DELIVERED_AT] = datetime.utcnow()

    def mark_as_read(self) -> None:
        self[Receipt.READ_AT] = datetime.utcnow()

    def is_delivered(self):
        return self.get(Receipt.DELIVERED_AT, None) is not None

    def is_read(self):
        return self.get(Receipt.READ_AT, None) is not None

    @classmethod
    def fetch_all_by_messages_and_user_id(cls, messages, user_id):
        receipt_ids = [Receipt.consistent_id(user_id,
                       message.id.key)
                       for message in messages]
        return cls.fetch_all(receipt_ids)
