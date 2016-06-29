import unittest
from unittest.mock import patch
from skygear.transmitter.encoding import deserialize_record

from ..pubsub import _publish_event


class TestPublishEvent(unittest.TestCase):

    def record(self):
        return deserialize_record({
            '_id': 'message/1',
            '_access': None,
            '_ownerID': 'user1',
            'conversation_id': 'conversation1',
            'body': 'hihi'
        })

    @patch('plugin.pubsub.publish')
    @patch('plugin.pubsub._get_channel_by_user_id')
    def test_pubsub_publish_called(
        self, mock_publish, mock_get_channel_by_user_id):
        mock_get_channel_by_user_id.return_value = 'channel1'
        _publish_event('user1', 'message', 'create', self.record())
        self.assertIs(mock_publish.call_count, 1)
