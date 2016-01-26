import unittest
from unittest.mock import patch, Mock

from chat_plugin import handle_message_after_save


class TestHandleMessageAfterSave(unittest.TestCase):

    def setUp(self):
        self.conn = None

    def record(self):
        return {
            'conversation_id': 'conversation1',
            'body': 'hihi'
        }

    def original_record(self):
        return {
            'conversation_id': 'conversation1',
            'body': 'hihi'
        }

    @patch('chat_plugin._publish_event')
    @patch('chat_plugin._get_conversation', Mock(return_value={
        'participant_ids': ['user1', 'user2']}))
    def test_publish_event_count(
            self, mock_publish_event):

        handle_message_after_save(
            self.record(), self.original_record(), self.conn)
        self.assertIs(mock_publish_event.call_count, 2)
