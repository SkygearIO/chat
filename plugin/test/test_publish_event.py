import unittest
from unittest.mock import patch

from chat_plugin import _publish_event


class TestPublishEvent(unittest.TestCase):

    @patch('skygear.pubsub.publish')
    @patch('chat_plugin._get_channel_by_user_id')
    def test_pubsub_publish_called(
        self, mock_publish, mock_get_channel_by_user_id):
        mock_get_channel_by_user_id.return_value = 'channel1'
        _publish_event('user1', 'message', 'create', {})
        self.assertIs(mock_publish.call_count, 1)
