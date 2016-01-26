
import unittest
import copy
from unittest.mock import Mock

import chat_plugin
from chat_plugin import handle_conversation_before_delete

class TestHandleConversationBeforeDelete(unittest.TestCase):

    def setUp(self):
        self.conn = None
        chat_plugin.current_user_id = Mock(return_value='user2')

    def record(self):
        return {
            'participant_ids': ['user1', 'user2'],
            'admin_ids': ['user1']
        }

    def test_delete_conversation_with_no_permission(self):
        with self.assertRaises(Exception) as cm:
            handle_conversation_before_delete(self.record(), self.conn)

    def test_delete_conversation_with_permission(self):
        record = self.record()
        record['admin_ids'] = ['user2']
        handle_conversation_before_delete(record, self.conn)
