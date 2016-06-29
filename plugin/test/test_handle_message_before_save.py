import unittest
from unittest.mock import Mock, patch
from skygear.transmitter.encoding import deserialize_record

from ..message import handle_message_before_save, SkygearChatException


class TestHandleMessageBeforeSave(unittest.TestCase):

    def setUp(self):
        self.conn = None

    def record(self):
        return deserialize_record({
            '_id': 'message/1',
            '_access': None,
            '_ownerID': 'user1',
            'conversation_id': 'conversation1',
            'body': 'hihi'
        })

    def original_record(self):
        return deserialize_record({
            '_id': 'message/1',
            '_access': None,
            '_ownerID': 'user1',
            'conversation_id': 'conversation1',
            'body': 'hihi'
        })

    @patch('plugin.message._get_conversation', Mock(
        return_value={'participant_ids': ['user1', 'user2'],}))
    @patch('plugin.utils.current_user_id', Mock(return_value='user1'))
    def test_original_record_is_not_none(self):
        with self.assertRaises(SkygearChatException) as cm:
            handle_message_before_save(
                self.record(), self.original_record(), self.conn)

    @patch('plugin.message._get_conversation', Mock(
        return_value={'participant_ids': ['user2', 'user3'],}))
    @patch('plugin.utils.current_user_id', Mock(return_value='user1'))
    def test_user_not_in_conversation(self):
        with self.assertRaises(SkygearChatException) as cm:
            handle_message_before_save(
                self.record(), None, self.conn)
