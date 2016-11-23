from datetime import datetime
from strict_rfc3339 import timestamp_to_rfc3339_utcoffset

import skygear
from skygear.pubsub import Hub
from skygear.skyconfig import config as skygear_config
from skygear.utils.context import current_user_id

from .exc import SkygearChatException


def publish_typing(conversation_id, evt, at):
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
    data = {}
    data[user_id] = {
        'event': evt,
        'at': timestamp_to_rfc3339_utcoffset(at.timestamp())
    }
    hub = Hub(api_key=skygear_config.app.api_key)
    hub.publish(conversation_id, data)


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

        return publish_typing(conversation_id, evt, dt)
