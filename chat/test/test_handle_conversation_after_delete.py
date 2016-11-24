import unittest
from unittest.mock import Mock, patch

from skygear.transmitter.encoding import deserialize_record

from ..conversation import handle_conversation_after_delete


class TestHandleConversationAfterDelete(unittest.TestCase):

    def setUp(self):
        self.conn = None

    def record(self):
        return deserialize_record({
            '_id': 'conversation/1',
            '_access': None,
            '_ownerID': 'user1',
            'participant_ids': ['user1', 'user2', 'user3'],
            'admin_ids': ['user1']
        })

    @patch('chat.conversation._publish_record_event')
    @patch('chat.conversation.skygear_config',
           Mock(return_value={'app': {'master_key': 'secret'}}))
    def test_publish_event_count_should_be_three(self, mock_publish_event):
        handle_conversation_after_delete(self.record(), self.conn)
        self.assertIs(mock_publish_event.call_count, 3)
