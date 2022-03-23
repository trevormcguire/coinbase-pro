from typing import *
from requests.auth import AuthBase
import time
import hmac
import hashlib
import base64


def get_timestamp():
    return time.time()

def sign(message, secret_key):
    message = message.encode('ascii')
    hmac_key = base64.b64decode(secret_key)
    signature = hmac.new(hmac_key, message, hashlib.sha256)
    signature_b64 = base64.b64encode(signature.digest()).decode('utf-8')
    return signature_b64


class CoinbaseAuth(AuthBase):
    """
    Authentication for Coinbase Pro
    """
    def __init__(self, sk: str, api_key: str, passphrase: str):
        self.secret_key = sk #ensure base64 encoded
        self.api_key = api_key
        self.passphrase = passphrase
    
    def __call__(self, request):
        timestamp = str(get_timestamp())
        body = request.body if request.body else ""        
        message = "".join([timestamp, request.method, request.path_url, body])
        signature = sign(message=message, secret_key=self.secret_key)
        auth_headers = {
            "Content-Type": "Application/JSON",
            "CB-ACCESS-SIGN": signature,
            "CB-ACCESS-TIMESTAMP": timestamp,
            "CB-ACCESS-KEY": self.api_key,
            "CB-ACCESS-PASSPHRASE": self.passphrase
        }
        request.headers.update(auth_headers)
        return request

