import requests, json, hmac, hashlib, time, base64, codecs
from requests.auth import AuthBase
import pandas as pd
from collections import deque
import math

def truncate(number, digits) -> float:
    stepper = 10.0 ** digits
    return math.trunc(stepper * number) / stepper

API_SECRET = 'vL83tlsKCU1a1+sV57t0PGO/Ow23WqU72airLjSTXv8uXJBcC9TtbJvtUX4D8qauwheW62BgXLtGYUW+QsoAKQ=='
API_KEY = '4a60aec62e8a0120bee80c0549699f6e'
API_PASS = 'kgs978a22jf'
api_url = 'https://api-public.sandbox.pro.coinbase.com/'
PAYMENT_METHOD_ID = ''
CASH_ACCOUNT = ''
BTC_ACCOUNT = ''
CASH_BALANCE = 0
BTC_BALANCE = 0
FEE_PERCENT = .005 # .5% fee per transaction
long_flag = False
cost_basis = 0


class CoinbaseAuth(AuthBase): # taken from Coinbase API docs to ensure protocol
    def __init__(self, api_key, secret_key, passphrase):
        self.api_key = api_key
        self.secret_key = secret_key
        self.passphrase = passphrase

    def __call__(self, request):
        timestamp = str(time.time())
        if isinstance(request.body,bytes): # request body will be in json format, which is stored as a bytes object
            request.body = request.body.decode('utf-8')
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

def buy(dataframe):
    print(dataframe)
    curr_ask = float(dataframe['Ask Price'].iloc[-1])
    max_order_size = min(float(CASH_BALANCE),10000*curr_ask)
    effective_order_size = truncate(max_order_size/(curr_ask*(1+FEE_PERCENT)),8)
    print(CASH_BALANCE)
    print(min(float(CASH_BALANCE),10000))
    print(curr_ask)
    print(float(dataframe['Ask Price'].iloc[-1]))
    print(min(float(CASH_BALANCE),10000*curr_ask)/curr_ask)
    print(truncate(min(float(CASH_BALANCE),10000*curr_ask)/curr_ask,8))
    order_details = {
        'type': 'limit',
        'side': 'buy',
        'product_id': 'BTC-USD',
        'price': curr_ask, # order limit is current ask price for fast fill 
        'size': effective_order_size # max trade size accounting for fee % and maximum size precision
    }
    order = requests.post(api_url + 'orders', json=order_details, auth=auth)
    if order.status_code != 200:
        print("BUY FAILED")
        text = json.dumps(order.json(), sort_keys=True, indent=4)
        print (text)
        #TODO: log error
    else:
        print("BUY SUCCEEDED")
        text = json.dumps(order.json(), sort_keys=True, indent=4)
        print (text)
        long_flag = True
        cost_basis = max_order_size/effective_order_size
    time.sleep(1) # allow time for order to fill
    orders = requests.get(api_url + 'orders', auth=auth)
    print(orders.json())
    if len(orders.json()) != 0:
        print('CANCELLING BUY')
        delete = requests.delete(api_url + 'orders', auth=auth)

def sell(dataframe):
    curr_bid = float(dataframe['Bid Price'].iloc[-1])
    max_order_size = min(float(BTC_BALANCE),10000)
    order_details = {
        'type': 'limit',
        'side': 'sell',
        'product_id': 'BTC-USD',
        'price': curr_bid, # order limit is current ask price for fast fill 
        'size': truncate(max_order_size/(1+FEE_PERCENT),8) # max trade size accounting for fee % and maximum size precision
    }
    order = requests.post(api_url + 'orders', json=order_details, auth=auth)
    if order.status_code != 200:
        print("SELL FAILED")
        text = json.dumps(order.json(), sort_keys=True, indent=4)
        print (text)
        #TODO: log error
    else:
        print("SELL SUCCEEDED")
        text = json.dumps(order.json(), sort_keys=True, indent=4)
        print (text)
        long_flag = False
    time.sleep(1) # allow time for order to fill
    orders = requests.get(api_url + 'orders', auth=auth)
    print(orders.json())
    if len(orders.json()) != 0:
        print('CANCELLING SELL')
        delete = requests.delete(api_url + 'orders', auth=auth)




order_details = {
    'type': 'limit',
    'side': 'buy',
    'product_id': 'BTC-USD',
    'price': 55000,
    'size': .00100001
}

order = requests.post(api_url + 'orders', json=order_details, auth=auth)
#order = requests.get(api_url + 'products', json=order_details, auth=auth)
text = json.dumps(order.json(), sort_keys=True, indent=4)
print(text)

#r = requests.post(api_url + 'orders', json=order_details, auth=auth)
#text = json.dumps(r.json(), sort_keys=True, indent=4)
#print (text)
#
#r = requests.get(api_url + 'orders', json=order_details, auth=auth)
#text = json.dumps(r.json(), sort_keys=True, indent=4)
#print (text)


BTC_data = deque(maxlen=200)

accounts = requests.get(api_url + 'accounts', auth=auth)
for account in accounts.json():
    if account['currency'] == 'USD':
        CASH_ACCOUNT = account['id']
        CASH_BALANCE = account['available']
    elif account['currency'] == 'BTC':
        BTC_ACCOUNT = account['id']
        BTC_BALANCE = account['available']

print(CASH_ACCOUNT)
print(CASH_BALANCE)
print(BTC_ACCOUNT)
print(BTC_BALANCE)

curr_data = requests.get(api_url + 'products/BTC-USD/book', auth=auth).json()
text = json.dumps(curr_data, sort_keys=True, indent=4)
print(text)

while(True):
    BTC_data.append([time.time(),curr_data['asks'][0][0],curr_data['asks'][0][1],curr_data['bids'][0][0],curr_data['bids'][0][1]])
    dataframe = pd.DataFrame(BTC_data)
    dataframe.columns = ['Unix Timestamp', 'Ask Price', 'Ask Size', 'Bid Price', 'Bid Size']

    dataframe['Average Price'] = dataframe.apply(lambda row: (float(row['Ask Price'])+float(row['Bid Price']))/2, axis=1)

    ShortEMA = dataframe['Average Price'].ewm(span=12,adjust=False).mean()
    LongEMA = dataframe['Average Price'].ewm(span=26,adjust=False).mean()
    MACD = ShortEMA - LongEMA
    signal = MACD.ewm(span=9,adjust=False).mean()

    dataframe['ShortEMA'] = ShortEMA
    dataframe['LongEMA'] = LongEMA
    dataframe['MACD'] = MACD
    dataframe['Signal'] = signal

    if long_flag == False and dataframe['MACD'].iloc[-1] > dataframe['Signal'].iloc[-1]:
        buy(dataframe)
    elif long_flag == True and dataframe['MACD'].iloc[-1] < dataframe['Signal'].iloc[-1]:
        sell(dataframe)

    time.sleep(1)
    print(BTC_data)
    print(dataframe)
    curr_data = requests.get(api_url + 'products/BTC-USD/book', auth=auth).json()
    print(dataframe['MACD'].iloc[-1])


#text = json.dumps(r.json(), sort_keys=True, indent=4)
#print (text)

r = requests.get(api_url + 'payment-methods',auth=auth)
text = json.dumps(r.json(), sort_keys=True, indent=4)
#print (text)

for method in r.json():
    if method['type'] == 'ach_bank_account':
        PAYMENT_METHOD_ID = method['id']

body = {
    'amount': 10,
    'currency': 'USD',
    'payment_method_id': PAYMENT_METHOD_ID
}

#r = requests.post(api_url + 'deposits/payment-method', json=body, auth=auth)
#text = json.dumps(r.json(), sort_keys=True, indent=4)
#print (text)


