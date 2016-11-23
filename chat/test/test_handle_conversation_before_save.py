import unittest
from unittest.mock import Mock, patch

from skygear.transmitter.encoding import deserialize_record

from ..conversation import (Conversation, SkygearChatException,
                            handle_conversation_before_save)


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

    def invalid_record(self):
        return deserialize_record({
            '_id': 'conversation/invalid',
            '_access': None,
            '_ownerID': 'user1',
            'participant_ids': ['user1', 'user2'],
            'admin_ids': ['user10']
        })

    def test_conversation_valiate_ok(self):
        Conversation(self.record()).validate()
        Conversation(self.original_record()).validate()

    def test_conversation_admins_not_paticipant(self):
        with self.assertRaises(SkygearChatException) as cm:
            Conversation(self.invalid_record()).validate()

    def test_conversation_paticipant_id_format(self):
        conv_with_wrong_user_id = deserialize_record({
            '_id': 'conversation/wronguserid',
            '_access': None,
            '_ownerID': 'user1',
            'participant_ids': ['user/user1', 'user/user2'],
            'admin_ids': []
        })
        with self.assertRaises(SkygearChatException) as cm:
            Conversation(conv_with_wrong_user_id).validate()

    @patch('chat.conversation.current_user_id', Mock(return_value="user1"))
    def test_with_valid_record(self):
        handle_conversation_before_save(
            self.record(), self.original_record(), self.conn)

    @patch('chat.conversation.current_user_id', Mock(return_value="user1"))
    def test_no_participants(self):
        record = self.record()
        record['participant_ids'] = []
        with self.assertRaises(SkygearChatException) as cm:
            handle_conversation_before_save(
                record, self.original_record(), self.conn)

    @patch('chat.conversation.current_user_id', Mock(return_value="user1"))
    def test_all_participant_is_admin_if_no_admins_provided(self):
        record = self.record()
        record['admin_ids'] = []
        handle_conversation_before_save(
            record, self.original_record(), self.conn)
        self.assertCountEqual(record['admin_ids'], record['participant_ids'])

    @patch('chat.conversation.current_user_id', Mock(return_value="user1"))
    def test_create_direct_message_for_others(self):
        record = self.record()
        record['participant_ids'] = ['user2', 'user3']
        record['is_direct_message'] = True
        with self.assertRaises(SkygearChatException) as cm:
            handle_conversation_before_save(
                record, None, self.conn)

    @patch('chat.conversation.current_user_id', Mock(return_value="user1"))
    def test_create_direct_message_with_three_participants(self):
        record = self.record()
        record['participant_ids'] = ['user1', 'user2', 'user3']
        record['is_direct_message'] = True
        with self.assertRaises(SkygearChatException) as cm:
            handle_conversation_before_save(
                record, None, self.conn)

    @patch('chat.conversation.current_user_id', Mock(return_value="user1"))
    def test_direct_message_should_have_admins_same_as_participants(self):
        record = self.record()
        record['is_direct_message'] = True
        handle_conversation_before_save(record, None, self.conn)
        self.assertCountEqual(record['admin_ids'], record['participant_ids'])
