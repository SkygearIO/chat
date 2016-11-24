from skygear.pubsub import Hub
from skygear.skyconfig import config as skygear_config

from .encoding import serialize_record
from .utils import _get_channel_by_user_id


def _publish_event(user_id, event, data=None):
    channel_name = _get_channel_by_user_id(user_id)
    if channel_name:
        hub = Hub(api_key=skygear_config.app.api_key)
        hub.publish(channel_name, {
            'event': event,
            'data': data
        })

def _publish_record_event(user_id,
                          record_type,
                          event,
                          record,
                          original_record=None):

    serialize_original_record = None
    if original_record is not None:
        serialize_original_record = serialize_record(original_record)
    _publish_event(user_id, event, {
        'type': 'record',
        'record_type': record_type,
        'record': serialize_record(record),
        'original_record': serialize_original_record
    })