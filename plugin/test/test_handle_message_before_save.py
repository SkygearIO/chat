import unittest
import copy
from unittest.mock import Mock

import chat_plugin
from chat_plugin import handle_message_before_save
from chat_plugin import SkygearChatException


class TestHandleMessageBeforeSave(unittest.TestCase):

    def setUp(self):
        self.conn = None
        chat_plugin.current_user_id = Mock(return_value='user1')
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

    def test_original_record_is_not_none(self):
        with self.assertRaises(SkygearChatException) as cm:
            handle_message_before_save(
                self.record(), self.original_record(), self.conn)

    def test_user_not_in_conversation(self):
        chat_plugin._get_conversation = Mock(return_value={
            'participant_ids': ['user2', 'user3'],
        })
        with self.assertRaises(SkygearChatException) as cm:
            handle_message_before_save(
                self.record(), None, self.conn)
