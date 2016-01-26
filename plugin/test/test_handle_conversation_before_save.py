import unittest
from unittest.mock import patch, Mock

from chat_plugin import handle_conversation_before_save, SkygearChatException


class TestHandleConversationBeforeSave(unittest.TestCase):

    def setUp(self):
        self.conn = None

    def record(self):
        return {
            'participant_ids': ['user1', 'user2'],
            'admin_ids': ['user1']
        }

    def original_record(self):
        return {
            'participant_ids': ['user1', 'user2'],
            'admin_ids': ['user1']
        }

    @patch('chat_plugin.current_user_id', Mock(return_value="user1"))
    def test_with_valid_record(self):
        handle_conversation_before_save(
            self.record(), self.original_record(), self.conn)

    @patch('chat_plugin.current_user_id', Mock(return_value="user1"))
    def test_no_participants(self):
        record = self.record()
        record['participant_ids'] = []
        with self.assertRaises(SkygearChatException) as cm:
            handle_conversation_before_save(
                record, self.original_record(), self.conn)

    @patch('chat_plugin.current_user_id', Mock(return_value="user1"))
    def test_no_admins(self):
        record = self.record()
        record['admin_ids'] = []
        with self.assertRaises(SkygearChatException) as cm:
            handle_conversation_before_save(
                record, self.original_record(), self.conn)

    @patch('chat_plugin.current_user_id', Mock(return_value="user1"))
    def test_create_direct_message_for_others(self):
        record = self.record()
        record['participant_ids'] = ['user2', 'user3']
        record['is_direct_message'] = True
        with self.assertRaises(SkygearChatException) as cm:
            handle_conversation_before_save(
                record, None, self.conn)

    @patch('chat_plugin.current_user_id', Mock(return_value="user1"))
    def test_create_direct_message_with_three_participants(self):
        record = self.record()
        record['participant_ids'] = ['user1', 'user2', 'user3']
        record['is_direct_message'] = True
        with self.assertRaises(SkygearChatException) as cm:
            handle_conversation_before_save(
                record, None, self.conn)

    @patch('chat_plugin.current_user_id', Mock(return_value="user1"))
    def test_direct_message_should_have_no_admin(self):
        record = self.record()
        record['is_direct_message'] = True
        handle_conversation_before_save(record, None, self.conn)
        self.assertTrue(record['admin_ids'] == [])
