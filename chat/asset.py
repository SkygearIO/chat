import base64
import hashlib
import hmac
from datetime import datetime, timedelta

from skygear.asset import get_signer


def sign_asset_url(name):
    signer = get_signer()
    return signer.sign(name) 
