import hashlib
import uuid

from skygear.container import SkygearContainer

from .utils import MASTER_KEY


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
                    'conversation': self.conversation_ref
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
