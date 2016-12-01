from skygear.models import Record
from skygear.pubsub import Hub
from skygear.skyconfig import config as skygear_config

from .encoding import serialize_record
from .utils import _get_channel_by_user_id


def _publish_event(user_id: str, event: str, data: dict = None) -> None:
    channel_name = _get_channel_by_user_id(user_id)
    if channel_name:
        hub = Hub(api_key=skygear_config.app.api_key)
        hub.publish(channel_name, {
            'event': event,
            'data': data
        })


def _publish_record_event(user_id: str,
                          record_type: str,
                          event: str,
                          record: Record) -> None:
    _publish_event(user_id, event, {
        'type': 'record',
        'record_type': record_type,
        'record': serialize_record(record)
    })
