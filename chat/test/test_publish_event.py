import unittest
from unittest.mock import Mock, patch

from skygear.transmitter.encoding import deserialize_record

from ..pubsub import _publish_record_event


class TestPublishEvent(unittest.TestCase):

    def record(self):
        return deserialize_record({
            '_id': 'message/1',
            '_access': None,
            '_ownerID': 'user1',
            'conversation_id': 'conversation1',
            'body': 'hihi'
        })

    @patch('chat.pubsub.Hub', autospec=True)
    @patch('chat.pubsub._get_channel_by_user_id',
           Mock(return_value='channel1'))
    @patch('chat.pubsub.skygear_config',
           Mock(return_value={'app': {'api_key': 'changeme'}}))
    def test_pubsub_publish_called(self, mock_hub):
        _publish_record_event('user1', 'message', 'create', self.record())
        self.assertEqual(len(mock_hub.method_calls), 1)
        self.assertEqual(mock_hub.method_calls[0][0], '().publish')
        self.assertEqual(mock_hub.method_calls[0][1][0], 'channel1')
        self.assertEqual(mock_hub.method_calls[0][1][1], {
            'event': 'create',
            'data': {
                'type': 'record',
                'record_type': 'message',
                'record': {
                    '_id': 'message/1',
                    '_access': None,
                    '_ownerID': 'user1',
                    'conversation_id': 'conversation1',
                    'body': 'hihi'
                },
                'original_record': None
            }
        })
