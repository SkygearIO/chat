from skygear.encoding import serialize_record as skyserialize

from .asset import sign_asset_url


def serialize_record(record):
    r = skyserialize(record)
    if 'attachment' in r:
        r['attachment']['$url'] = sign_asset_url(r['attachment']['$name'])
    return r
