import hashlib
import uuid

from psycopg2.extensions import AsIs

import skygear
from skygear.container import SkygearContainer
from skygear.options import options as skyoptions
from skygear.utils import db
from skygear.utils.context import current_user_id

from .utils import _get_schema_name


class UserConversation():
    def __init__(self, conversation, participant_id, master_key=None):
        if master_key is None:
            master_key = skyoptions.masterkey

        self.conversation = conversation
        self.participant_id = participant_id
        self.master_key = master_key

    def get_conversation_ref(self):
        return {
            '$type': 'ref',
            '$id': 'conversation/' + self.conversation.record.id._key
        }

    def get_consistent_hash(self):
        seed = self.conversation.record.id._key + self.participant_id
        sha = hashlib.sha256(bytes(seed, 'utf8'))
        return uuid.UUID(bytes=sha.digest()[0:16])

    def create(self):
        container = SkygearContainer(api_key=self.master_key,
                                     user_id=self.participant_id)
        container.send_action('record:save', {
            'database_id': '_public',
            'records': [{
                '_id': 'user_conversation/' + str(self.get_consistent_hash()),
                '_access': [],
                'user': {
                    '$type': 'ref',
                    '$id': 'user/' + self.participant_id
                },
                'conversation': self.get_conversation_ref(),
                'unread_count': 0
            }]
        })

    def delete(self):
        container = SkygearContainer(api_key=self.master_key,
                                     user_id=self.participant_id)
        container.send_action('record:delete', {
            'database_id': '_public',
            'ids': ['user_conversation/' + str(self.get_consistent_hash())]
        })


def total_unread(user_id=None):
    if user_id is None:
        user_id = current_user_id()
    with db.conn() as conn:
        cur = conn.execute('''
            SELECT COUNT(*), SUM("unread_count")
            FROM %(schema_name)s.user_conversation
            WHERE
                "unread_count" > 0 AND
                "user" = %(user_id)s
            ''', {
                'schema_name': AsIs(_get_schema_name()),
                'user_id': user_id
            }
        )
        r = cur.first()
        conversation_count = r[0]
        message_count = r[1]
    return {
        'conversation': conversation_count,
        'message': message_count
    }


def register_user_conversation_lambdas(settings):
    @skygear.op("chat:total_unread", auth_required=True, user_required=True)
    def total_unread_lambda():
        return total_unread()
