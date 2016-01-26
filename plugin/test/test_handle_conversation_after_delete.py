import unittest
from unittest.mock import patch

from chat_plugin import handle_conversation_after_delete


class TestHandleConversationAfterDelete(unittest.TestCase):

    def setUp(self):
        self.conn = None

    def record(self):
        return {
            'participant_ids': ['user1', 'user2', 'user3'],
            'admin_ids': ['user1']
        }

    @patch('chat_plugin._publish_event')
    def test_publish_event_count_should_be_three(self, mock_publish_event):
        handle_conversation_after_delete(self.record(), self.conn)
        self.assertIs(mock_publish_event.call_count, 3)
