import requests, json, hmac, hashlib, time, base64, codecs
from requests.auth import AuthBase

API_SECRET = 'vL83tlsKCU1a1+sV57t0PGO/Ow23WqU72airLjSTXv8uXJBcC9TtbJvtUX4D8qauwheW62BgXLtGYUW+QsoAKQ=='
API_KEY = '4a60aec62e8a0120bee80c0549699f6e'
API_PASS = 'kgs978a22jf'
api_url = 'https://api-public.sandbox.pro.coinbase.com/'


class CoinbaseAuth(AuthBase): # taken from Coinbase API docs to ensure protocol
    def __init__(self, api_key, secret_key, passphrase):
        self.api_key = api_key
        self.secret_key = secret_key
        self.passphrase = passphrase

    def __call__(self, request):
        timestamp = str(time.time())
        message = timestamp + request.method + request.path_url + (request.body or '')
        hmac_key = base64.b64decode(self.secret_key)
        signature = hmac.new(hmac_key, codecs.encode(message,'utf-8'), hashlib.sha256)
        signature_b64 = base64.b64encode(signature.digest())

        request.headers.update({
            'CB-ACCESS-SIGN': signature_b64,
            'CB-ACCESS-TIMESTAMP': timestamp,
            'CB-ACCESS-KEY': self.api_key,
            'CB-ACCESS-PASSPHRASE': self.passphrase,
            'Content-Type': 'application/json'
        })
        return request

auth = CoinbaseAuth(API_KEY, API_SECRET, API_PASS)
r = requests.get(api_url + 'accounts', auth=auth)
text = json.dumps(r.json(), sort_keys=True, indent=4)
print (text)


