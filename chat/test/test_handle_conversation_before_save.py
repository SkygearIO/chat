import unittest
from unittest.mock import Mock, patch

from skygear.transmitter.encoding import deserialize_record

from ..conversation import (Conversation, SkygearChatException,
                            handle_conversation_before_save)


class TestHandleConversationBeforeSave(unittest.TestCase):

    def setUp(self):
        self.conn = None
        self.patchers = [
            patch('chat.conversation.skygear_config',
                  Mock(return_value={'app': {'master_key': 'secret'}})),
            patch('chat.conversation.current_user_id',
                  Mock(return_value="user1")),
        ]
        for each_patcher in self.patchers:
            each_patcher.start()

    def tearDown(self):
        for each_patcher in self.patchers:
            each_patcher.stop()

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

    def test_with_valid_record(self):
        handle_conversation_before_save(
            self.record(), self.original_record(), self.conn)

    def test_no_participants(self):
        record = self.record()
        record['participant_ids'] = []
        with self.assertRaises(SkygearChatException) as cm:
            handle_conversation_before_save(
                record, self.original_record(), self.conn)

    def test_all_participant_is_admin_if_no_admins_provided(self):
        record = self.record()
        record['admin_ids'] = []
        handle_conversation_before_save(
            record, self.original_record(), self.conn)
        self.assertCountEqual(record['admin_ids'], record['participant_ids'])

    def test_create_direct_message_for_others(self):
        record = self.record()
        record['participant_ids'] = ['user2', 'user3']
        record['is_direct_message'] = True
        with self.assertRaises(SkygearChatException) as cm:
            handle_conversation_before_save(
                record, None, self.conn)

    def test_filling_participant_count(self):
        record = self.record()
        handle_conversation_before_save(record, None, self.conn)
        self.assertEqual(record['participant_count'],
                         len(record['participant_ids']))

    @patch('chat.conversation.SkygearContainer', autospect=True)
    def test_distinct_by_participants_check_valid(self, mock_container_class):
        mock_container = Mock()
        mock_container.send_action.return_value = {'result': []}
        mock_container_class.side_effect = lambda **kwargs : mock_container

        record = self.record()
        record['distinct_by_participants'] = True
        handle_conversation_before_save(record, None, self.conn)
        mock_container.send_action.assert_called_with('record:query', {
            'database_id': '_public',
            'limit': 1,
            'record_type': 'conversation',
            'predicate': [
                'and',
                [
                    'eq',
                    {'$type': 'keypath', '$val': 'distinct_by_participants'},
                    True
                ],
                [
                    'eq',
                    {'$type': 'keypath', '$val': 'participant_count'},
                    2
                ],
                [
                    'neq',
                    {'$type': 'keypath', '$val': '_id'},
                    '1'
                ],
                [
                    'in',
                    'user1',
                    {'$type': 'keypath', '$val': 'participant_ids'}
                ],
                [
                    'in',
                    'user2',
                    {'$type': 'keypath', '$val': 'participant_ids'}
                ]
            ]
        })

    @patch('chat.conversation.SkygearContainer', autospect=True)
    def test_distinct_by_participants_check_invalid(self, mock_container_class):
        mock_container = Mock()
        mock_container.send_action.return_value = {'result': [{
            '_id': 'conversation/2',
            '_access': None,
            '_ownerID': 'user2',
            'participant_ids': ['user1', 'user2'],
            'admin_ids': ['user2']
        }]}
        mock_container_class.side_effect = lambda **kwargs : mock_container

        record = self.record()
        record['distinct_by_participants'] = True
        with self.assertRaises(SkygearChatException) as cm:
            handle_conversation_before_save(record, None, self.conn)
