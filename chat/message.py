from psycopg2.extensions import AsIs

from skygear.utils import db

from .exc import AlreadyDeletedException
from .predicate import Predicate
from .pubsub import _publish_record_event
from .query import Query
from .record import ChatRecord
from .user_conversation import UserConversation
from .utils import _get_schema_name, to_rfc3339_or_none


class Message(ChatRecord):
    record_type = 'message'

    def delete(self) -> None:
        """
        Soft-delete a message
        - Mark message as deleted
        - Update last_message and last_read_message
        """

        if self['deleted']:
            raise AlreadyDeletedException()

        self['deleted'] = True
        self.save()

    def getReceiptList(self):
        """
        Returns a list of message receipt statuses.
        """
        receipts = list()
        with db.conn() as conn:
            cur = conn.execute('''
                SELECT receipt.user, read_at, delivered_at
                FROM %(schema_name)s.receipt
                WHERE
                    "message" = %(message_id)s
                ''', {
                    'schema_name': AsIs(_get_schema_name()),
                    'message_id': self.id.key
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
        cur = conn.execute('''
            WITH
              read_count AS (
                SELECT DISTINCT COUNT(receipt.user) as count
                FROM %(schema_name)s.receipt
                WHERE message = %(message_id)s
                    AND read_at IS NOT NULL
              ),
              participant_count AS (
                SELECT count(1) as count
                FROM %(schema_name)s.user_conversation
                WHERE conversation = %(conversation_id)s
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
                'message_id': self.id.key,
                'conversation_id': self.conversation_id
            }
        )

        row = cur.fetchone()
        if row is not None:
            self['_updated_at'] = row[0]
            self['message_status'] = row[1]

    def notifyParticipants(self, event_type='update') -> None:
        result = UserConversation.\
            fetch_all_by_conversation_id(self.conversation_id)
        participants = [row['user'].recordID.key for row in result]
        for each_participant in participants:
            _publish_record_event(each_participant,
                                  "message",
                                  event_type,
                                  self)

    @property
    def conversation_id(self):
        return self['conversation'].recordID.key

    @classmethod
    def fetch_all_by_conversation_id(cls, conversation_id,
                                     limit, before_time, order):
        database = cls._get_database()
        predicate = Predicate(conversation__eq=conversation_id,
                              deleted__eq=False)
        if before_time is not None:
            predicate = predicate & Predicate(_created_at__lt=before_time)
        query = Query('message', predicate=predicate, limit=limit)
        if order != 'edited_at':
            order = '_created_at'
        query.add_order(order, 'desc')
        return database.query(query)

    @classmethod
    def fetch_all_by_conversation_id_and_seq(cls,
                                             conversation_id,
                                             from_seq,
                                             to_seq):
        database = cls._get_database()
        predicate = Predicate(seq__lte=to_seq,
                              conversation__eq=conversation_id,
                              deleted__eq=False)
        if from_seq >= 0:
            predicate = predicate & Predicate(seq__gte=from_seq)

        query = Query('message', predicate=predicate, limit=None)
        return database.query(query)
