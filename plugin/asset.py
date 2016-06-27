import os
import base64
from datetime import datetime, timedelta
import hashlib
import hmac

ASSET_PREFIX_KEY = 'ASSET_STORE_URL_PREFIX'
ASSET_SIGN_SECRET_KEY = 'ASSET_STORE_SECRET'

_config = os.environ


def sign_asset_url(name):
    """
    This helper function generates a signed S3 URL to access the Asset
    specified by the name parameter.
    """
    expired_at = int((datetime.now()+timedelta(minutes=15)).timestamp())
    expired_at_str = str(expired_at)

    hasher = hmac.new(_sign_secret().encode('utf-8'), digestmod=hashlib.sha256)
    hasher.update(name.encode('utf-8'))
    hasher.update(expired_at_str.encode('utf-8'))

    # TODO(limouren): investigate why python generates hash with an extra byte
    # compared with golang
    signature = base64.urlsafe_b64encode(hasher.digest()[:-1]).decode('utf-8')

    return '%s/%s?expiredAt=%s&signature=%s' % (
        _asset_prefix(),
        name,
        expired_at_str,
        signature
    )


def _asset_prefix():
    return os.getenv(ASSET_PREFIX_KEY, 'http://localhost:3000/')


def _sign_secret():
    return os.getenv(ASSET_SIGN_SECRET_KEY, '')
