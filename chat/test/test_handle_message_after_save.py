import unittest
from unittest.mock import Mock, patch

from skygear.transmitter.encoding import deserialize_record

from ..exc import SkygearChatException
from ..message_handlers import handle_message_after_save


class TestHandleMessageAfterSave(unittest.TestCase):

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

    @patch('chat.message._publish_record_event')
    @patch('chat.message_handlers._get_schema_name', Mock(return_value='app_dev'))
    @patch('chat.message._get_conversation', Mock(return_value={
        'participant_ids': ['user1', 'user2']}))
    def test_publish_event_count(self, mock_publish_event):
        conn = Mock()
        handle_message_after_save(self.record(), None, conn)
        self.assertIs(mock_publish_event.call_count, 2)
        self.assertIs(conn.execute.call_count, 2)
        self.assertIs(conn.execute.call_args_list[0][0][1]['conversation_id'], '1')
        self.assertIs(conn.execute.call_args_list[1][0][1]['conversation_id'], '1')
        self.assertIs(conn.execute.call_args_list[1][0][1]['message_id'], '1')
