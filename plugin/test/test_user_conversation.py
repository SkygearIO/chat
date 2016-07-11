import unittest
from unittest.mock import patch
from skygear.transmitter.encoding import deserialize_record

from ..conversation import UserConversation


class TestUserConversation(unittest.TestCase):
    def conversation(self):
        return deserialize_record({
            '_id': 'conversation/1',
            '_access': None,
            '_ownerID': 'user1',
            'participant_ids': ['user1', 'user2'],
            'admin_ids': ['user1']
        })

    def test_consistent_hash(self):
        uc = UserConversation(self.conversation().id)
        r = uc.consistent_hash('itwillbesha256')
        r2 = uc.consistent_hash('itwillbesha256')
        another = uc.consistent_hash('another')
        self.assertEqual(str(r), str(r2))
        self.assertNotEqual(str(r), str(another))

    @patch('plugin.user_conversation.SkygearContainer', autospec=True)
    def test_create(self, container):
        uc = UserConversation(self.conversation().id)
        uc.create(['userid'])
        self.assertEqual(len(container.method_calls), 1)
        self.assertEqual(container.method_calls[0][0], '().send_action')
        self.assertEqual(container.method_calls[0][1], (
            'record:save',
            {
                'database_id': '_private',
                'records': [{
                    '_id':
                    'user_conversation/5e0069ae-1fe3-9680-5512-332b363bbc73',
                    'conversation': {'$id': 'conversation/1', '$type': 'ref'},
                    'user': {'$id': 'user/userid', '$type': 'ref'},
                    'unread_count': 0
                }]
            }
        ))

    @patch('plugin.user_conversation.SkygearContainer', autospec=True)
    def test_create_multiple(self, container):
        uc = UserConversation(self.conversation().id)
        uc.create(['userid', 'userid2'])
        self.assertEqual(len(container.method_calls), 2)

    @patch('plugin.user_conversation.SkygearContainer', autospec=True)
    def test_delete(self, container):
        uc = UserConversation(self.conversation().id)
        uc.delete(['userid'])
        self.assertEqual(len(container.method_calls), 1)
        self.assertEqual(container.method_calls[0][0], '().send_action')
        self.assertEqual(container.method_calls[0][1], (
            'record:delete',
            {
                'database_id': '_private',
                'ids': ['user_conversation/5e0069ae-1fe3-9680-5512-332b363bbc73']
            }
        ))

    @patch('plugin.user_conversation.SkygearContainer', autospec=True)
    def test_delete_multiple(self, container):
        uc = UserConversation(self.conversation().id)
        uc.delete(['userid', 'userid2'])
        self.assertEqual(len(container.method_calls), 2)
