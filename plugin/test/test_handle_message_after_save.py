import unittest
import copy
from unittest.mock import Mock

import chat_plugin
from chat_plugin import handle_message_after_save


class TestHandleMessageAfterSave(unittest.TestCase):

    def setUp(self):
        self.conn = None
        self._publish_event_mock = Mock()
        chat_plugin._publish_event = self._publish_event_mock
        chat_plugin._get_conversation = Mock(return_value={
            'participant_ids': ['user1', 'user2'],
        })

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

    def test_publish_event_count(self):
        handle_message_after_save(self.record(), self.original_record(), self.conn)
        self.assertIs(self._publish_event_mock.call_count, 2)
