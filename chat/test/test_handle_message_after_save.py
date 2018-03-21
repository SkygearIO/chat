import unittest
from unittest.mock import Mock, patch

from skygear.encoding import deserialize_record

from ..conversation import Conversation
from ..user_conversation import UserConversation
from ..message import Message
from ..exc import SkygearChatException
from ..message_handlers import handle_message_after_save


def get_mock_conversation():
    c = Conversation.new('1', 'user1')
    c['participant_ids'] = []
    return c


class TestHandleMessageAfterSave(unittest.TestCase):

    def setUp(self):
        self.conn = None
        self.patchers = [
            patch('chat.utils.skyoptions',
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

    @patch('chat.message.UserConversation.fetch_all_by_conversation_id',
           Mock(return_value=[UserConversation.new(Conversation.new('a', 'user1'), 'user1'),
                              UserConversation.new(Conversation.new('a', 'user2'), 'user2')]))
    @patch('chat.message._publish_record_event')
    @patch('chat.message_handlers._get_schema_name', Mock(return_value='app_dev'))
    @patch('chat.message.UserConversation.fetch_one', Mock(return_value=None))
    @patch('chat.message_handlers.Conversation.fetch_one', Mock(return_value=get_mock_conversation()))
    @patch('chat.message_handlers.send_after_message_sent_hook', Mock())
    def test_publish_event_count(self, mock_publish_event):
        conn = Mock()
        handle_message_after_save(self.record(), None, conn)
        self.assertIs(mock_publish_event.call_count, 1)
        self.assertIs(conn.execute.call_count, 3)
        self.assertIs(conn.execute.call_args_list[0][0][1]['conversation_id'], '1')
        self.assertIs(conn.execute.call_args_list[1][0][1]['conversation_id'], '1')
        self.assertIs(conn.execute.call_args_list[2][0][1]['conversation_id'], '1')
        self.assertIs(conn.execute.call_args_list[2][0][1]['message_id'], '1')
