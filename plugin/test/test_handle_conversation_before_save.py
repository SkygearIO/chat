import unittest
from unittest.mock import patch, Mock
from skygear.transmitter.encoding import deserialize_record

from ..conversation import handle_conversation_before_save, SkygearChatException


class TestHandleConversationBeforeSave(unittest.TestCase):

    def setUp(self):
        self.conn = None

    def record(self):
        return deserialize_record({
            '_id': 'conversation/1',
            '_access': None,
            '_ownerID': 'user1',
            'participant_ids': ['user1', 'user2'],
            'admin_ids': ['user1']
        })


    def original_record(self):
        return deserialize_record({
            '_id': 'conversation/1',
            '_access': None,
            '_ownerID': 'user1',
            'participant_ids': ['user1', 'user2'],
            'admin_ids': ['user1']
        })

    @patch('plugin.conversation.current_user_id', Mock(return_value="user1"))
    def test_with_valid_record(self):
        handle_conversation_before_save(
            self.record(), self.original_record(), self.conn)

    @patch('plugin.conversation.current_user_id', Mock(return_value="user1"))
    def test_no_participants(self):
        record = self.record()
        record['participant_ids'] = []
        with self.assertRaises(SkygearChatException) as cm:
            handle_conversation_before_save(
                record, self.original_record(), self.conn)

    @patch('plugin.conversation.current_user_id', Mock(return_value="user1"))
    def test_all_participant_is_admin_if_no_admins_provided(self):
        record = self.record()
        record['admin_ids'] = []
        handle_conversation_before_save(
            record, self.original_record(), self.conn)
        self.assertCountEqual(record['admin_ids'], record['participant_ids'])

    @patch('plugin.conversation.current_user_id', Mock(return_value="user1"))
    def test_create_direct_message_for_others(self):
        record = self.record()
        record['participant_ids'] = ['user2', 'user3']
        record['is_direct_message'] = True
        with self.assertRaises(SkygearChatException) as cm:
            handle_conversation_before_save(
                record, None, self.conn)

    @patch('plugin.conversation.current_user_id', Mock(return_value="user1"))
    def test_create_direct_message_with_three_participants(self):
        record = self.record()
        record['participant_ids'] = ['user1', 'user2', 'user3']
        record['is_direct_message'] = True
        with self.assertRaises(SkygearChatException) as cm:
            handle_conversation_before_save(
                record, None, self.conn)

    @patch('plugin.conversation.current_user_id', Mock(return_value="user1"))
    def test_direct_message_should_have_admins_same_as_participants(self):
        record = self.record()
        record['is_direct_message'] = True
        handle_conversation_before_save(record, None, self.conn)
        self.assertCountEqual(record['admin_ids'], record['participant_ids'])
