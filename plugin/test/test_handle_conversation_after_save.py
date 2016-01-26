import unittest
import copy
from unittest.mock import Mock

import chat_plugin
from chat_plugin import handle_conversation_after_save

class TestHandleConversationAfterSave(unittest.TestCase):

    def setUp(self):
        self.conn = None
        self.mock_publish_event = Mock()
        chat_plugin._publish_event = self.mock_publish_event

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

    def test_newly_created_conversation(self):
        handle_conversation_after_save(self.record(), None, self.conn)
        self.assertTrue(self.mock_publish_event.call_count == 2)

    def test_newly_created_conversation_2(self):
        handle_conversation_after_save(
            self.record(), self.original_record(), self.conn)
        self.assertTrue(self.mock_publish_event.call_count == 3)
