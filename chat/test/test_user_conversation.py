import unittest
from unittest.mock import Mock, patch

from skygear.transmitter.encoding import deserialize_record

from ..conversation import Conversation, UserConversation


class TestUserConversation(unittest.TestCase):
    def setUp(self):
        self.patchers = [
            patch('chat.conversation.skygear_config',
                  Mock(return_value={'app': {'master_key': 'secret'}})),
            patch('chat.user_conversation.skygear_config',
                  Mock(return_value={'app': {'master_key': 'secret'}})),
        ]
        for each_patcher in self.patchers:
            each_patcher.start()

    def tearDown(self):
        for each_patcher in self.patchers:
            each_patcher.stop()

    def conversation(self):
        return deserialize_record({
            '_id': 'conversation/1',
            '_access': None,
            '_ownerID': 'user1',
            'participant_ids': ['user1', 'user2'],
            'admin_ids': ['user1']
        })

    def test_consistent_hash(self):
        c = Conversation(self.conversation())
        uc1 = UserConversation(c, 'userid1')
        uc2 = UserConversation(c, 'userid1')
        uc3 = UserConversation(c, 'userid2')
        r1 = uc1.get_consistent_hash()
        r2 = uc2.get_consistent_hash()
        r3 = uc3.get_consistent_hash()
        self.assertEqual(str(r1), str(r2))
        self.assertNotEqual(str(r1), str(r3))

    @patch('chat.user_conversation.SkygearContainer', autospec=True)
    def test_create(self, container):
        c = Conversation(self.conversation())
        uc = UserConversation(c, 'userid')
        uc.create()
        self.assertEqual(len(container.method_calls), 1)
        self.assertEqual(container.method_calls[0][0], '().send_action')
        self.assertEqual(container.method_calls[0][1], (
            'record:save',
            {
                'database_id': '_public',
                'records': [{
                    '_id':
                    'user_conversation/5e0069ae-1fe3-9680-5512-332b363bbc73',
                    '_access': [],
                    'conversation': {'$id': 'conversation/1', '$type': 'ref'},
                    'user': {'$id': 'user/userid', '$type': 'ref'},
                    'unread_count': 0
                }]
            }
        ))

    @patch('chat.user_conversation.SkygearContainer', autospec=True)
    def test_delete(self, container):
        c = Conversation(self.conversation())
        uc = UserConversation(c, 'userid')
        uc.delete()
        self.assertEqual(len(container.method_calls), 1)
        self.assertEqual(container.method_calls[0][0], '().send_action')
        self.assertEqual(container.method_calls[0][1], (
            'record:delete',
            {
                'database_id': '_public',
                'ids': ['user_conversation/5e0069ae-1fe3-9680-5512-332b363bbc73']
            }
        ))
