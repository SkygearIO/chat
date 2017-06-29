from psycopg2.extensions import AsIs

from skygear.container import SkygearContainer
from skygear.error import ResourceNotFound
from skygear.models import Record
from skygear.options import options as skyoptions
from skygear.transmitter.encoding import deserialize_record, serialize_record
from skygear.utils import db
from skygear.utils.context import current_user_id

from .exc import AlreadyDeletedException, SkygearChatException
from .pubsub import _publish_record_event
from .utils import (_get_conversation, _get_schema_name, fetch_records,
                    get_key_from_object, to_rfc3339_or_none)


class Message:
    def __init__(self):
        self.record = None
        self.conversationRecord = None

    @classmethod
    def from_dict(cls, result_dict):
        obj = cls()
        obj.record = deserialize_record(result_dict)
        return obj

    @classmethod
    def fetch(cls, arg: [str]):
        """
        Fetch the message(s) from skygear.

        The conversation record is also fetched using eager load.
        """
        if not isinstance(arg, list):
            arg = [arg]
        message_ids = [get_key_from_object(x) for x in arg]

        container = SkygearContainer(api_key=skyoptions.masterkey,
                                     user_id=current_user_id())

        messages = fetch_records(container, '_union', 'message',
                                 message_ids, Message.from_dict)
        if len(messages) == 0:
            raise SkygearChatException('no messages found',
                                       code=ResourceNotFound)

        conversation_ids = [message.record['conversation'].recordID.key
                            for message in messages]

        print("conversation_ids to be queried:[%s]" %
              ",".join(conversation_ids))

        conversations = fetch_records(container, '_public',
                                      'conversation', conversation_ids,
                                      lambda x: deserialize_record(x))

        conversations_dict = {}
        for conversation in conversations:
            key = conversation.id.key
            conversations_dict[key] = conversation

        for message in messages:
            conversation_id = message.record['conversation'].recordID.key
            if conversation_id not in conversations_dict:
                raise SkygearChatException(
                      "conversation %s from message %s not found." %
                      (conversation_id, message.record.id.key))
            message.conversationRecord = conversations_dict[conversation_id]
        return messages

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
