import hashlib
import uuid
from datetime import datetime

from skygear.container import SkygearContainer
from skygear.models import Record, RecordID, Reference
from skygear.options import options as skyoptions
from skygear.transmitter.encoding import deserialize_record, serialize_record
from skygear.utils.context import current_user_id

from .utils import fetch_records, get_key_from_object


class Receipt:
    DELIVERED_AT = 'delivered_at'
    READ_AT = 'read_at'

    def __init__(self, user_id: str, message_id: str):
        if not isinstance(user_id, str):
            raise ValueError('user_id is not str')
        if not isinstance(message_id, str):
            raise ValueError('message_id is not str')
        self.record = Record(
            RecordID('receipt', Receipt.consistent_id(user_id, message_id)),
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
        self.record[Receipt.DELIVERED_AT] = datetime.utcnow()

    def mark_as_read(self) -> None:
        self.record[Receipt.READ_AT] = datetime.utcnow()

    def is_delivered(self):
        return self.record.get(Receipt.DELIVERED_AT, None) is not None

    def is_read(self):
        return self.record.get(Receipt.READ_AT, None) is not None

    @classmethod
    def fetch(cls, arg: [str]):
        """
        Fetch the receipts(s) from skygear.
        """
        if not isinstance(arg, list):
            arg = [arg]
        receipt_ids = [get_key_from_object(x) for x in arg]

        container = SkygearContainer(api_key=skyoptions.masterkey,
                                     user_id=current_user_id())

        records = fetch_records(container, '_public', 'receipt',
                                receipt_ids,
                                lambda x:
                                deserialize_record(x))
        receipts = []
        for record in records:
            obj = cls(record['user'].recordID.key,
                      record['message'].recordID.key)
            obj.record = record
            receipts.append(obj)

        return receipts


class ReceiptCollection(list):
    """
    ReceiptCollection is a collection to provide batch saving function
    to many receipts.
    """
    def save(self) -> None:
        """
        Save the collection of receipts to the database. This function
        does nothing if there is nothing in the collection.
        """
        if not len(self):
            return

        records_to_save = [
            serialize_record(receipt.record)
            for receipt in self
        ]

        container = SkygearContainer(api_key=skyoptions.masterkey,
                                     user_id=current_user_id())
        container.send_action('record:save', {
            'database_id': '_public',
            'records': records_to_save,
            'atomic': True
        })
