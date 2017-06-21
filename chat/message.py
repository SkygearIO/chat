from psycopg2.extensions import AsIs

from skygear.container import SkygearContainer
from skygear.error import ResourceNotFound
from skygear.models import Record, RecordID, Reference
from skygear.options import options as skyoptions
from skygear.transmitter.encoding import deserialize_record, serialize_record
from skygear.utils import db
from skygear.utils.context import current_user_id

from .exc import AlreadyDeletedException, SkygearChatException
from .pubsub import _publish_record_event
from .utils import _get_conversation, _get_schema_name, to_rfc3339_or_none


class Message:
    def __init__(self):
        self.record = None
        self.conversationRecord = None

    @classmethod
    def fetch(cls, message_id: str):
        """
        Fetch the message from skygear.

        The conversation record is also fetched using eager load.
        """
        # FIXME checking should not be necessary, passing correct type
        # is the responsibility of the caller.
        # message_id can be Reference, recordID or string
        if isinstance(message_id, Reference):
            message_id = message_id.recordID.key
        if isinstance(message_id, RecordID):
            message_id = message_id.key
        if not isinstance(message_id, str):
            raise ValueError()

        container = SkygearContainer(api_key=skyoptions.masterkey,
                                     user_id=current_user_id())
        response = container.send_action(
            'record:query',
            {
                'database_id': '_union',
                'record_type': 'message',
                'limit': 1,
                'sort': [],
                'count': False,
                'predicate': [
                    'eq', {
                        '$type': 'keypath',
                        '$val': '_id'
                    },
                    message_id
                ]
            }
        )

        if 'error' in response:
            raise SkygearChatException(response['error'])

        if len(response['result']) == 0:
            raise SkygearChatException('no messages found',
                                       code=ResourceNotFound)

        obj = cls()
        messageDict = response['result'][0]
        obj.record = deserialize_record(messageDict)
        # Conversation is in publicDB, do cannot transient include
        print(obj.record['conversation'].recordID.key)
        response = container.send_action(
            'record:query',
            {
                'database_id': '_public',
                'record_type': 'conversation',
                'limit': 1,
                'sort': [],
                'count': False,
                'predicate': [
                    'eq', {
                        '$type': 'keypath',
                        '$val': '_id'
                    },
                    obj.record['conversation'].recordID.key
                ]
            }
        )
        if len(response['result']) == 0:
            raise SkygearChatException("no conversation found")
        conversationDict = response['result'][0]
        obj.conversationRecord = deserialize_record(conversationDict)
        return obj

    @classmethod
    def from_record(cls, record):
        """
        Create a message from a record. This function do not make
        external calls.
        """
        obj = cls()
        obj.record = record
        return obj

    def delete(self) -> None:
        """
        Soft-delete a message
        - Mark message as deleted
        - Update last_message and last_read_message
        """

        if self.record['deleted']:
            raise AlreadyDeletedException()

        self.record['deleted'] = True
        self.save()

    def fetchConversationRecord(self) -> Record:
        """
        Fetch conversation record. This is required if the Message
        is created using a Record rather than fetching the Record
        from the database.
        """
        conversation_id = self.record['conversation'].recordID.key
        self.conversationRecord = _get_conversation(conversation_id)
        return self.conversationRecord

    def getReceiptList(self):
        """
        Returns a list of message receipt statuses.
        """
        receipts = list()
        with db.conn() as conn:
            cur = conn.execute('''
                SELECT user, read_at, delivered_at
                FROM %(schema_name)s.receipt
                WHERE
                    "message" = %(message_id)s
                ''', {
                    'schema_name': AsIs(_get_schema_name()),
                    'message_id': self.record.id.key
                }
            )

            for row in cur:
                receipts.append({
                    'user': row['user'],
                    'read_at': to_rfc3339_or_none(row['read_at']),
                    'delivered_at': to_rfc3339_or_none(row['delivered_at'])
                })
        return receipts

    def updateMessageStatus(self, conn) -> bool:
        """
        Update the message status field by querying the database for
        all receipt statuses.
        """
        if not self.conversationRecord:
            raise Exception('no conversation record')

        cur = conn.execute('''
            WITH
              read_count AS (
                SELECT DISTINCT COUNT(user) as count
                FROM %(schema_name)s.receipt
                WHERE message = %(message_id)s
                    AND read_at IS NOT NULL
              ),
              participant_count AS (
                SELECT participant_count as count
                FROM %(schema_name)s.conversation
                WHERE _id = %(conversation_id)s
              )
            UPDATE %(schema_name)s.message
            SET _updated_at = NOW(),
                message_status =
                  CASE
                    WHEN read_count.count = 0 THEN 'delivered'
                    WHEN read_count.count < participant_count.count
                        THEN 'some_read'
                    ELSE 'all_read'
                  END
            FROM read_count, participant_count
            WHERE _id = %(message_id)s
            RETURNING _updated_at, message_status
            ''', {
                'schema_name': AsIs(_get_schema_name()),
                'message_id': self.record.id.key,
                'conversation_id': self.conversationRecord.id.key
            }
        )

        row = cur.fetchone()
        if row is not None:
            self.record['_updated_at'] = row[0]
            self.record['message_status'] = row[1]

    def notifyParticipants(self, event_type='update') -> None:
        if not self.conversationRecord:
            fetched = self.fetchConversationRecord()
            if fetched is None:
                raise SkygearChatException('no conversation record',
                                           code=ResourceNotFound)
        participants = set(self.conversationRecord['participant_ids'])
        for each_participant in participants:
            _publish_record_event(each_participant,
                                  "message",
                                  event_type,
                                  self.record)

    def save(self) -> None:
        """
        Save the Message record to the database.
        """
        container = SkygearContainer(api_key=skyoptions.masterkey,
                                     user_id=current_user_id())
        container.send_action('record:save', {
            'database_id': '_private',
            'records': [serialize_record(self.record)],
            'atomic': True
        })
