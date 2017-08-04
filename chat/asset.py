import base64
import hashlib
import hmac
from datetime import datetime, timedelta

from skygear.settings import settings


# TODO: This does not fit cloud deployment. Need to be removed.
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

    signature = base64.urlsafe_b64encode(hasher.digest()).decode('utf-8')

    return '%s/%s?expiredAt=%s&signature=%s' % (
        _asset_prefix(),
        name,
        expired_at_str,
        signature
    )


def _asset_prefix():
    return settings.chat.asset_store_url_prefix


def _sign_secret():
    return settings.chat.asset_store_secret
