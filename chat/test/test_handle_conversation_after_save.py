import unittest
from unittest.mock import Mock, patch

from skygear.transmitter.encoding import deserialize_record

from ..conversation import pubsub_conversation_after_save


class TestHandleConversationAfterSave(unittest.TestCase):

    def setUp(self):
        self.conn = None
        self.patcher = patch('chat.conversation.skygear_config',
                             Mock(return_value={
                                'app': {'master_key': 'secret'}
                             }))
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

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
            'participant_ids': ['user2', 'user3'],
            'admin_ids': ['user1']
        })

    @patch('chat.conversation._publish_record_event')
    def test_pubsub_newly_created_conversation(self, mock_publish_event):
        pubsub_conversation_after_save(self.record(), None, self.conn)
        self.assertIs(mock_publish_event.call_count, 2)

    @patch('chat.conversation._publish_record_event')
    def test_pubsub_newly_created_conversation_with_original_record(
            self, mock_publish_event):
        pubsub_conversation_after_save(
            self.record(), self.original_record(), self.conn)
        self.assertIs(mock_publish_event.call_count, 3)
