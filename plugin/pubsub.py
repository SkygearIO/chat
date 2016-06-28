from skygear.pubsub import publish

from .encoding import serialize_record
from .utils import _get_channel_by_user_id

def _publish_event(participant_id, record_type, event_type, record,
                   original_record=None):
    serialize_orig_record = None
    if original_record is not None:
        serialize_orig_record = serialize_record(original_record)
    data = {
        'record_type': record_type,
        'event_type': event_type,
        'record': serialize_record(record),
        'original_record': serialize_orig_record
    }

    channel_name = _get_channel_by_user_id(participant_id)

    if channel_name:
        publish(channel_name, data)
