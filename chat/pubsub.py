from skygear.models import Record
from skygear.options import options as skyoptions

from .encoding import serialize_record
from .hub import Hub
from .utils import _get_channels_by_user_ids


def _publish_event(user_ids: [], event: str, data: dict = None) -> None:
    if not isinstance(user_ids, list):
        user_ids = user_ids
    if len(user_ids) == 0:
        return
    channel_names = _get_channels_by_user_ids(user_ids)
    if channel_names:
        hub = Hub(api_key=skyoptions.apikey)
        hub.publish(channel_names, {
            'event': event,
            'data': data
        })


def _publish_record_event(user_ids: [],
                          record_type: str,
                          event: str,
                          record: Record) -> None:
    if len(user_ids) == 0:
        return
    _publish_event(user_ids, event, {
        'event_type': event,
        'type': 'record',
        'record_type': record_type,
        'record': serialize_record(record)
    })
