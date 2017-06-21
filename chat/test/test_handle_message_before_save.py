import unittest
from unittest.mock import Mock, patch

from skygear.transmitter.encoding import deserialize_record

from ..exc import SkygearChatException
from ..message_handlers import handle_message_before_save


class TestHandleMessageBeforeSave(unittest.TestCase):

    def setUp(self):
        self.conn = None
        self.patchers = [
            patch('chat.conversation.skyoptions',
                  Mock(return_value={'masterkey': 'secret'})),
            patch('chat.user_conversation.skyoptions',
                  Mock(return_value={'masterkey': 'secret'})),
        ]
        for each_patcher in self.patchers:
            each_patcher.start()

    def tearDown(self):
        for each_patcher in self.patchers:
            each_patcher.stop()

    def record(self):
        return deserialize_record({
            '_id': 'message/1',
            '_access': None,
            '_ownerID': 'user1',
            'conversation': {
                '$type': 'ref',
                '$id': 'conversation/1'
            },
            'body': 'hihi'
        })

    def original_record(self):
        return deserialize_record({
            '_id': 'message/1',
            '_access': None,
            '_ownerID': 'user1',
            'conversation': {
                '$type': 'ref',
                '$id': 'conversation/1'
            },
            'body': 'hihi'
        })

    @patch('chat.message._get_conversation', Mock(
        return_value={'participant_ids': ['user1', 'user2'],}))
    def test_original_record_is_not_none(self):
        with self.assertRaises(SkygearChatException) as cm:
            handle_message_before_save(
                self.record(), self.original_record(), self.conn)

    @patch('chat.message._get_conversation', Mock(
        return_value={'participant_ids': ['user2', 'user3'],}))
    def test_user_not_in_conversation(self):
        with self.assertRaises(SkygearChatException) as cm:
            handle_message_before_save(
                self.record(), None, self.conn)
