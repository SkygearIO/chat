import unittest
from unittest.mock import Mock, patch

from chat_plugin import handle_message_before_save, SkygearChatException


class TestHandleMessageBeforeSave(unittest.TestCase):

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

    @patch('chat_plugin._get_conversation', Mock(
        return_value={'participant_ids': ['user1', 'user2'],}))
    @patch('chat_plugin.current_user_id', Mock(return_value='user1'))
    def test_original_record_is_not_none(self):
        with self.assertRaises(SkygearChatException) as cm:
            handle_message_before_save(
                self.record(), self.original_record(), self.conn)

    @patch('chat_plugin._get_conversation', Mock(
        return_value={'participant_ids': ['user2', 'user3'],}))
    @patch('chat_plugin.current_user_id', Mock(return_value='user1'))
    def test_user_not_in_conversation(self):
        with self.assertRaises(SkygearChatException) as cm:
            handle_message_before_save(
                self.record(), None, self.conn)
