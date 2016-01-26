import unittest
from unittest.mock import patch

from chat_plugin import handle_conversation_after_save

class TestHandleConversationAfterSave(unittest.TestCase):

    def setUp(self):
        self.conn = None

    def record(self):
        return {
            'participant_ids': ['user1', 'user2'],
            'admin_ids': ['user1']
        }

    def original_record(self):
        return {
            'participant_ids': ['user2', 'user3'],
            'admin_ids': ['user1']
        }

    @patch('chat_plugin._publish_event')
    def test_newly_created_conversation(self, mock_publish_event):
        handle_conversation_after_save(self.record(), None, self.conn)
        self.assertIs(mock_publish_event.call_count, 2)

    @patch('chat_plugin._publish_event')
    def test_newly_created_conversation_with_original_record(
            self, mock_publish_event):
        handle_conversation_after_save(
            self.record(), self.original_record(), self.conn)
        self.assertIs(mock_publish_event.call_count, 3)
