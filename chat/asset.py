from skygear.asset import get_signer


def sign_asset_url(name):
    signer = get_signer()
    return signer.sign(name)
