import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, call, patch

from skygear.models import Record, RecordID
from skygear.encoding import deserialize_record

from ..conversation import Conversation
from ..user_conversation import UserConversation
from ..message import Message
from ..exc import InvalidGetMessagesConditionArgumentException
from ..message_handlers import handle_message_after_save


from ..message_handlers import get_messages

class TestHandleGetMessages(unittest.TestCase):

    def mock_fetch_messages_func(self, conversation_id, limit,
                                 before_time=None, before_message_id=None,
                                 after_time=None, after_message_id=None,
                                 order=None, deleted=False):
        base_created_at = datetime(2017, 11, 8, 0, 0, tzinfo=timezone.utc)
        owner_id = 'u1'
        acl = None

        if deleted:
            return [Record(RecordID('message', 'rd1'), owner_id, acl,
                    created_at=base_created_at - timedelta(hours=1))]
        else:
            if conversation_id == 'empty_conversation':
                return []
            else:
                return [Record(RecordID('message', 'r3'), owner_id, acl,
                               created_at=base_created_at - timedelta(days=1)),
                        Record(RecordID('message', 'r2'), owner_id, acl,
                               created_at=base_created_at - timedelta(days=2)),
                        Record(RecordID('message', 'r1'), owner_id, acl,
                               created_at=base_created_at - timedelta(days=3))]

    @patch('chat.message_handlers.Message.fetch_all_by_conversation_id')
    @patch('chat.message_handlers.Conversation.exists', Mock(return_value=True))
    def test_get_emptied_messages(self, mock_fetch_messages):
        conversation_id = 'empty_conversation'

        mock_fetch_messages.side_effect = self.mock_fetch_messages_func

        result = get_messages(conversation_id, 3)

        mock_fetch_messages.assert_has_calls([
            call('empty_conversation', 3,
                 after_time=None, before_time=None, order=None),
            call('empty_conversation', 999999,
                 after_time=None, before_time=None,
                 deleted=True, order=None)
        ])

        self.assertIs(len(result['results']), 0)
        self.assertIs(len(result['deleted']), 1)

    @patch('chat.message_handlers.Message.fetch_all_by_conversation_id')
    @patch('chat.message_handlers.Conversation.exists', Mock(return_value=True))
    def test_get_messages_without_params(self, mock_fetch_messages):
        conversation_id = 'c1'

        mock_fetch_messages.side_effect = self.mock_fetch_messages_func

        result = get_messages(conversation_id, 3)

        mock_fetch_messages.assert_has_calls([
            call('c1', 3,
                 after_time=None, before_time=None, order=None),
            call('c1', 999999,
                 after_time='2017-11-05T00:00:00Z',
                 before_time=None,
                 deleted=True, order=None)
        ])

        self.assertIs(len(result['results']), 3)
        self.assertIs(len(result['deleted']), 1)

    @patch('chat.message_handlers.Message.fetch_all_by_conversation_id')
    @patch('chat.message_handlers.Conversation.exists', Mock(return_value=True))
    def test_get_messages_with_before_time(self, mock_fetch_messages):
        conversation_id = 'c1'

        mock_fetch_messages.side_effect = self.mock_fetch_messages_func

        result = get_messages(conversation_id, 3, before_time='2017-11-12T00:00:00Z')

        mock_fetch_messages.assert_has_calls([
            call('c1', 3,
                 after_time=None, before_time='2017-11-12T00:00:00Z', order=None),
            call('c1', 999999,
                 after_time='2017-11-05T00:00:00Z',
                 before_time='2017-11-12T00:00:00Z',
                 deleted=True, order=None)
        ])

        self.assertIs(len(result['results']), 3)
        self.assertIs(len(result['deleted']), 1)

    @patch('chat.message_handlers.Message.fetch_all_by_conversation_id')
    @patch('chat.message_handlers.Conversation.exists', Mock(return_value=True))
    def test_get_messages_with_after_time(self, mock_fetch_messages):
        conversation_id = 'c1'

        mock_fetch_messages.side_effect = self.mock_fetch_messages_func

        result = get_messages(conversation_id, 3, after_time='2017-11-03T00:00:00Z')

        mock_fetch_messages.assert_has_calls([
            call('c1', 3,
                 after_time='2017-11-03T00:00:00Z', before_time=None, order=None),
            call('c1', 999999,
                 after_time='2017-11-03T00:00:00Z',
                 before_time='2017-11-07T00:00:00Z',
                 deleted=True, order=None)
        ])

        self.assertIs(len(result['results']), 3)
        self.assertIs(len(result['deleted']), 1)

    @patch('chat.message_handlers.Message.fetch_all_by_conversation_id')
    @patch('chat.message_handlers.Conversation.exists', Mock(return_value=True))
    def test_get_messages_with_time_range(self, mock_fetch_messages):
        conversation_id = 'c1'

        mock_fetch_messages.side_effect = self.mock_fetch_messages_func

        result = get_messages(conversation_id, 3,
                              after_time='2017-11-03T00:00:00Z',
                              before_time='2017-11-12T00:00:00Z')

        mock_fetch_messages.assert_has_calls([
            call('c1', 3,
                 after_time='2017-11-03T00:00:00Z',
                 before_time='2017-11-12T00:00:00Z',
                 order=None),
            call('c1', 999999,
                 after_time='2017-11-03T00:00:00Z',
                 before_time='2017-11-12T00:00:00Z',
                 deleted=True, order=None)
        ])

        self.assertIs(len(result['results']), 3)
        self.assertIs(len(result['deleted']), 1)

    @patch('chat.message_handlers.Message.fetch_all_by_conversation_id')
    @patch('chat.message_handlers.Conversation.exists', Mock(return_value=True))
    def test_get_messages_with_message_id(self, mock_fetch_messages):
        conversation_id = 'c1'

        mock_fetch_messages.side_effect = self.mock_fetch_messages_func

        result = get_messages(conversation_id, 3, before_message_id='r4')

        mock_fetch_messages.assert_has_calls([
            call('c1', 3,
                 after_message_id=None, before_message_id='r4', order=None),
            call('c1', 999999,
                 after_message_id='r1',
                 before_message_id='r4',
                 deleted=True, order=None)
        ])

        self.assertIs(len(result['results']), 3)
        self.assertIs(len(result['deleted']), 1)

    @patch('chat.message_handlers.Conversation.exists', Mock(return_value=True))
    def test_get_messages_with_both_time_and_message_id(self):
        conversation_id = 'c1'

        with self.assertRaises(InvalidGetMessagesConditionArgumentException) as cm:
            get_messages(conversation_id, 3,
                         before_time='2017-11-12T00:00:00Z',
                         before_message_id='r4')

