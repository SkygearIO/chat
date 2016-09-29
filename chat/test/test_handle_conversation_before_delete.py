import unittest
from unittest.mock import patch

from skygear.transmitter.encoding import deserialize_record

from ..conversation import handle_conversation_before_delete, SkygearChatException

class TestHandleConversationBeforeDelete(unittest.TestCase):

    def setUp(self):
        self.conn = None

    def record(self):
        return deserialize_record({
            '_id': 'conversation/1',
            '_access': None,
            '_ownerID': 'user1',
            'participant_ids': ['user1', 'user2'],
            'admin_ids': ['user1']
        })

    @patch('chat.conversation.current_user_id')
    def test_delete_conversation_with_no_permission(self, mock_current_user_id):
        mock_current_user_id.return_value = 'user2'
        with self.assertRaises(SkygearChatException) as cm:
            handle_conversation_before_delete(self.record(), self.conn)

    @patch('chat.conversation.current_user_id')
    def test_delete_conversation_with_permission(self, mock_current_user_id):
        mock_current_user_id.return_value = 'user1'
        handle_conversation_before_delete(self.record(), self.conn)
