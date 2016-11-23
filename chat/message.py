from psycopg2.extensions import AsIs

from skygear.container import SkygearContainer
from skygear.models import Record, RecordID, Reference
from skygear.skyconfig import config as skygear_config
from skygear.transmitter.encoding import deserialize_record, serialize_record
from skygear.utils import db
from skygear.utils.context import current_user_id

from .exc import SkygearChatException
from .utils import _get_conversation, _get_schema_name, to_rfc3339_or_none


class Message:
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

        container = SkygearContainer(api_key=skygear_config.app.api_key)
        response = container.send_action(
            'record:query',
            {
                'database_id': '_public',
                'record_type': 'message',
                'limit': 1,
                'sort': [],
                'include': {
                    'conversation': {
                        '$type': 'keypath',
                        '$val': 'conversation_id'
                    }
                },
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
            raise SkygearChatException("no conversation found")

        obj = cls()
        messageDict = response['result'][0]
        obj.record = deserialize_record(messageDict)
        conversationDict = messageDict['_transient']['conversation']
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

    def fetch_conversation_record(self) -> Record:
        """
        Fetch conversation record. This is required if the Message
        is created using a Record rather than fetching the Record
        from the database.
        """
        conversation_id = self.record['conversation_id'].recordID.key
        self.conversationRecord = _get_conversation(conversation_id)
        return self.conversationRecord

    def getReceiptList(self):
        """
        Returns a list of message receipt statuses.
        """
        receipts = list()
        with db.conn() as conn:
            cur = conn.execute('''
                SELECT user_id, read_at, delivered_at
                FROM %(schema_name)s.receipt
                WHERE
                    "message_id" = %(message_id)s
                ''', {
                    'schema_name': AsIs(_get_schema_name()),
                    'message_id': self.record.id.key
                }
            )

            for row in cur:
                receipts.append({
                    'user_id': row['user_id'],
                    'read_at': to_rfc3339_or_none(row['read_at']),
                    'delivered_at': to_rfc3339_or_none(row['delivered_at'])
                })
        return receipts

    def updateConversationStatus(self, conn) -> bool:
        """
        Update the conversation status field by querying the database for
        all receipt statuses.
        """
        if not self.conversationRecord:
            raise Exception('no conversation record')

        cur = conn.execute('''
            SELECT DISTINCT user_id
            FROM %(schema_name)s.receipt
            WHERE message_id = %(message_id)s AND read_at IS NOT NULL
            ''', {
                'schema_name': AsIs(_get_schema_name()),
                'message_id': self.record.id.key
            }
        )

        read_users = set([row[0] for row in cur if row[0]])
        participants = set(self.conversationRecord['participant_ids'])
        if len(read_users) == 0:
            new_status = 'delivered'
        elif read_users + set([self.record.created_by]) > participants:
            new_status = 'some_read'
        else:
            new_status = 'all_read'

        if new_status == self.record.get('conversation_status', None):
            return False

        self.record['conversation_status'] = new_status
        return True

    def save(self) -> None:
        """
        Save the Message record to the database.
        """
        container = SkygearContainer(api_key=skygear_config.app.master_key,
                                     user_id=current_user_id())
        container.send_action('record:save', {
            'database_id': '_public',
            'records': [serialize_record(self.record)],
            'atomic': True
        })
