import unittest
import copy
from unittest.mock import Mock

import chat_plugin
from chat_plugin import handle_conversation_after_delete

class TestHandleConversationAfterDelete(unittest.TestCase):

    def setUp(self):
        self.conn = None
        self.mock_publish_event = Mock()
        chat_plugin._publish_event = self.mock_publish_event

    def record(self):
        return {
            'participant_ids': ['user1', 'user2', 'user3'],
            'admin_ids': ['user1']
        }

    def test_publish_event_count_should_be_three(self):
        handle_conversation_after_delete(self.record(), self.conn)
        self.assertIs(self.mock_publish_event.call_count, 3)
