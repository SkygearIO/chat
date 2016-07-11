import hashlib
import uuid

from psycopg2.extensions import AsIs

import skygear
from skygear.container import SkygearContainer

from .utils import MASTER_KEY, schema_name


@skygear.before_save("user_conversation", async=False)
def populate_unread_count(record, orig, conn):
    if orig is None:
        return
    if record.get('last_read_message') == orig.get('last_read_message'):
        return

    conversation = record.get('conversation')
    last_read_message = record.get('last_read_message')
    if last_read_message is None:
        return

    cur = conn.execute('''
        SELECT COUNT(*)
        FROM %(schema_name)s.message
        WHERE
            "conversation_id" = %(conversation_id)s AND
            "_created_at" > (
                SELECT "_created_at" FROM %(schema_name)s.message
                WHERE "_id" = %(last_read_message)s
            )
        ''', {
        'schema_name': AsIs(schema_name),
        'conversation_id': conversation.recordID.key,
        'last_read_message': last_read_message.recordID.key,
    }
    )
    r = cur.first()
    record['unread_count'] = r[0]
    return record


class UserConversation():
    def __init__(self, conversation_id: 'RecordID', master_key=MASTER_KEY):
        self.conversation_id = conversation_id
        self.conversation_ref = {
            '$type': 'ref',
            '$id': 'conversation/' + conversation_id._key
        }
        self.master_key = master_key

    def consistent_hash(self, user_id):
        seed = self.conversation_id._key + user_id
        sha = hashlib.sha256(bytes(seed, 'utf8'))
        return uuid.UUID(bytes=sha.digest()[0:16])

    def create(self, user_ids: [str]):
        for user_id in user_ids:
            container = SkygearContainer(api_key=MASTER_KEY,
                                         user_id=user_id)
            uc_uid = self.consistent_hash(user_id)
            container.send_action('record:save', {
                'database_id': '_private',
                'records': [{
                    '_id': 'user_conversation/' + str(uc_uid),
                    'user': {
                        '$type': 'ref',
                        '$id': 'user/' + user_id
                    },
                    'conversation': self.conversation_ref,
                    'unread_count': 0
                }]
            })

    def delete(self, user_ids: [str]):
        for user_id in user_ids:
            container = SkygearContainer(api_key=MASTER_KEY,
                                         user_id=user_id)
            uc_uid = self.consistent_hash(user_id)
            container.send_action('record:delete', {
                'database_id': '_private',
                'ids': ['user_conversation/' + str(uc_uid)]
            })
