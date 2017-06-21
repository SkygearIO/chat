import hashlib
import uuid
from datetime import datetime

from skygear.container import SkygearContainer
from skygear.models import Record, RecordID, Reference
from skygear.options import options as skyoptions
from skygear.transmitter.encoding import serialize_record
from skygear.utils.context import current_user_id


class Receipt:
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
        self.record['delivered_at'] = datetime.utcnow()

    def mark_as_read(self) -> None:
        self.record['read_at'] = datetime.utcnow()


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


def create_delivered_receipts(
    user_id: str,
    message_ids: [str]
) -> ReceiptCollection:
    """
    This is a helper function to create a collection of delivered receipts.
    """
    receipts = ReceiptCollection()
    for message_id in message_ids:
        receipt = Receipt(user_id, message_id)
        receipt.mark_as_delivered()
        receipts.append(receipt)
    return receipts


def create_read_receipts(
    user_id: str,
    message_ids: [str]
) -> ReceiptCollection:
    """
    This is a helper function to create a collection of read receipts.
    """
    receipts = ReceiptCollection()
    for message_id in message_ids:
        receipt = Receipt(user_id, message_id)
        receipt.mark_as_delivered()  # message that is read is also delivered
        receipt.mark_as_read()
        receipts.append(receipt)
    return receipts
