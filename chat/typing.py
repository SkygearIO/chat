from datetime import datetime

from strict_rfc3339 import timestamp_to_rfc3339_utcoffset

import skygear
from skygear.transmitter.encoding import _RecordEncoder
from skygear.utils.context import current_user_id

from .conversation import Conversation
from .exc import SkygearChatException
from .pubsub import _publish_event


def publish_typing(conversation, evt, at):
    """
    {
      'userid': {
        'event': 'begin',
        'at': '20161116T78:44:00Z'
      },
      'userid2': {
        'event': 'begin',
        'at': '20161116T78:44:00Z'
      }
    }
    """
    user_id = current_user_id()
    channels = conversation['participant_ids']
    data = {}
    data['user/' + user_id] = {
        'event': evt,
        'at': timestamp_to_rfc3339_utcoffset(at.timestamp())
    }
    encoder = _RecordEncoder()
    for user_id in channels:
        _publish_event(user_id, 'typing', {
            encoder.encode_id(conversation.id): data
        })
    return {'status': 'OK'}


def register_typing_lambda(settings):
    @skygear.op("chat:typing", auth_required=True, user_required=True)
    def publish_typing_lambda(conversation_id, evt, at):
        if evt not in ['begin', 'pause', 'finished']:
            raise SkygearChatException('Typing event is invalid')
        try:
            # FIXME: datetime format should be from py-skygear
            dt = datetime.strptime(at, '%Y-%m-%dT%H:%M:%S.%fZ')
        except ValueError:
            raise SkygearChatException('Event time is not in correct format')
        c = Conversation.fetch_one(conversation_id)
        return publish_typing(c, evt, dt)
