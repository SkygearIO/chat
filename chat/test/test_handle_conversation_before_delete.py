import unittest
from unittest.mock import Mock, patch

from skygear.transmitter.encoding import deserialize_record

from ..conversation import (SkygearChatException,
                            handle_conversation_before_delete)


class TestHandleConversationBeforeDelete(unittest.TestCase):

    def setUp(self):
        self.conn = None
        self.patcher = patch('chat.conversation.skygear_config',
                             Mock(return_value={
                                'app': {'master_key': 'secret'}
                             }))
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    def record(self):
        return deserialize_record({
            '_id': 'conversation/1',
            '_access': None,
            '_ownerID': 'user1',
            'participant_ids': ['user1', 'user2'],
            'admin_ids': ['user1']
        })

    @patch('chat.conversation.current_user_id',
           Mock(return_value='user2'))
    def test_delete_conversation_with_no_permission(self):
        with self.assertRaises(SkygearChatException) as cm:
            handle_conversation_before_delete(self.record(), self.conn)

    @patch('chat.conversation.current_user_id',
           Mock(return_value='user1'))
    def test_delete_conversation_with_permission(self):
        handle_conversation_before_delete(self.record(), self.conn)
