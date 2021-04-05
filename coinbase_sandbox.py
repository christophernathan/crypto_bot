import requests, json, hmac, hashlib, time, base64, codecs
from requests.auth import AuthBase
import pandas as pd
from collections import deque
import math
import csv
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

def truncate(number, digits) -> float:
    stepper = 10.0 ** digits
    return math.trunc(stepper * number) / stepper

API_SECRET = os.environ.get('API_SECRET')
API_KEY = os.environ.get('API_KEY')
API_PASS = os.environ.get('API_PASS')
api_url = 'https://api-public.sandbox.pro.coinbase.com/'
PAYMENT_METHOD_ID = ''
CASH_ACCOUNT = ''
BTC_ACCOUNT = ''
CASH_BALANCE = 0
BTC_BALANCE = 0
FEE_PERCENT = .005
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

def recordActivity(side,price,btc_quantity,usd_value,fees,cost_basis,profit):
    with open('trade_activity.csv', mode='a') as trade_activity:
        record_activity = csv.writer(trade_activity, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        timestamp = int(time.time())
        dateTime = datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        record_activity.writerow([timestamp,dateTime,side,price,btc_quantity,usd_value,fees,cost_basis,profit])

def recordError(side,status_code,reason):
    with open('trade_errors.csv', mode='a') as trade_errors:
        record_error = csv.writer(trade_errors, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        timestamp = int(time.time())
        dateTime = datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        record_error.writerow([timestamp,dateTime,side,status_code,reason])

def updateFeePercent(): # assuming Taker fee classification to be safe. Percents current as of 4/3/21
    global FEE_PERCENT

    fee_table = {
        10000: .005,
        50000: .0035,
        100000: .0025,
        1000000: .002,
        10000000: .0018,
        50000000: .0015,
        100000000: .001,
        300000000: .0007,
        500000000: .0006,
        1000000000: .0005
    }
    timestamp = int(time.time())
    start_time = timestamp-2592000 # number of seconds in last 30 days
    activity = pd.read_csv('trade_activity.csv')
    frame = pd.DataFrame(activity)
    total = 0
    frame = frame.iloc[::-1]
    for index,row in frame.iterrows():
        if row['Unix Timestamp'] > start_time:
            total += row['USD Value']
        else:
            break
    for key in fee_table:
        if total < key:
            FEE_PERCENT = fee_table[key]
            return
    FEE_PERCENT = fee_table[list(fee_table)[-1]]

def buy(dataframe):
    global long_flag, cost_basis
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
    order_id = order.json()['id']
    if order.status_code != 200:
        recordError('BUY',order.status_code,order.json()['message'])
    else:
        print("BUY SUCCEEDED")
        text = json.dumps(order.json(), sort_keys=True, indent=4)
        print (text)
        long_flag = True
        cost_basis = max_order_size/effective_order_size
        print('COST BASIS AFTER BUY: ', cost_basis)
        usd_value = effective_order_size*curr_ask
        fee = max_order_size-(effective_order_size*curr_ask)
        recordActivity('BUY',curr_ask,effective_order_size,usd_value,fee,cost_basis,0)
        updateFeePercent()
    time.sleep(1) # allow time for order to fill
    orders = requests.get(api_url + 'orders', auth=auth)
    print(orders.json())
    if len(orders.json()) != 0:
        print('CANCELLING BUY')
        delete = requests.delete(api_url + 'orders', auth=auth)

def sell(dataframe):
    global long_flag
    curr_bid = float(dataframe['Bid Price'].iloc[-1])
    final_cost_basis = ((cost_basis*BTC_BALANCE)+(curr_bid*BTC_BALANCE*FEE_PERCENT))/BTC_BALANCE
    max_order_size = min(float(BTC_BALANCE),10000)
    effective_order_size = truncate(max_order_size/(1+FEE_PERCENT),8)
    order_details = {
        'type': 'limit',
        'side': 'sell',
        'product_id': 'BTC-USD',
        'price': curr_bid, # order limit is current ask price for fast fill 
        'size': effective_order_size # max trade size accounting for fee % and maximum size precision
    }
    order = requests.post(api_url + 'orders', json=order_details, auth=auth)
    order_id = order.json()['id']
    if order.status_code != 200:
        recordError('SELL',order.status_code,order.json()['message'])
    else:
        print("SELL SUCCEEDED")
        text = json.dumps(order.json(), sort_keys=True, indent=4)
        print (text)
        long_flag = False
        usd_value = effective_order_size*curr_bid
        fee = (max_order_size-effective_order_size)*curr_bid
        profit = (curr_bid-final_cost_basis)*effective_order_size
        recordActivity('SELL',curr_bid,effective_order_size,usd_value,fee,final_cost_basis,profit)
        updateFeePercent()
    time.sleep(1) # allow time for order to fill
    orders = requests.get(api_url + 'orders', auth=auth)
    print(orders.json())
    if len(orders.json()) != 0:
        print('CANCELLING SELL')
        delete = requests.delete(api_url + 'orders', auth=auth)


#order_details = {
#    'type': 'limit',
#    'side': 'buy',
#    'product_id': 'BTC-USD',
#    'price': 55000,
#    'size': .00100001
#}
#
#order = requests.post(api_url + 'orders', json=order_details, auth=auth)
##order = requests.get(api_url + 'products', json=order_details, auth=auth)
#text = json.dumps(order.json(), sort_keys=True, indent=4)
#print(text)

#r = requests.post(api_url + 'orders', json=order_details, auth=auth)
#text = json.dumps(r.json(), sort_keys=True, indent=4)
#print (text)
#
#r = requests.get(api_url + 'orders', json=order_details, auth=auth)
#text = json.dumps(r.json(), sort_keys=True, indent=4)
#print (text)

def initializeAccountInfo():
    global CASH_ACCOUNT, BTC_ACCOUNT, CASH_BALANCE, BTC_BALANCE
    accounts = requests.get(api_url + 'accounts', auth=auth)
    for account in accounts.json():
        if account['currency'] == 'USD':
            CASH_ACCOUNT = account['id']
            CASH_BALANCE = float(account['available'])
        elif account['currency'] == 'BTC':
            BTC_ACCOUNT = account['id']
            BTC_BALANCE = float(account['available'])

def updateAccountBalances():
    global CASH_BALANCE, BTC_BALANCE
    accounts = requests.get(api_url + 'accounts', auth=auth)
    for account in accounts.json():
        if account['currency'] == 'USD':
            CASH_BALANCE = float(account['available'])
        elif account['currency'] == 'BTC':
            BTC_BALANCE = float(account['available'])

def getMarketData(BTC_data):
    curr_data = requests.get(api_url + 'products/BTC-USD/book', auth=auth).json()
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
    return dataframe

def initializeCostBasis():
    global cost_basis
    activity = pd.read_csv('trade_activity.csv')
    frame = pd.DataFrame(activity)
    if frame.iloc[-1]['Trade Side'] == 'BUY':
        cost_basis = frame.iloc[-1]['Cost Basis']


auth = CoinbaseAuth(API_KEY, API_SECRET, API_PASS)

order_details = {
        'type': 'limit',
        'side': 'buy',
        'product_id': 'BTC-USD',
        'price': 0, # order limit is current ask price for fast fill 
        'size': .00000000001 # max trade size accounting for fee % and maximum size precision
    }
order = requests.post(api_url + 'orders', json=order_details, auth=auth)
print(order.json())

def bot():
    global CASH_ACCOUNT, BTC_ACCOUNT, CASH_BALANCE, BTC_BALANCE, long_flag, cost_basis

    BTC_data = deque(maxlen=200)

    updateFeePercent()
    print(FEE_PERCENT)

    initializeCostBasis()
    initializeAccountInfo()

    print(CASH_ACCOUNT)
    print(CASH_BALANCE)
    print(BTC_ACCOUNT)
    print(BTC_BALANCE)

    curr_data = requests.get(api_url + 'products/BTC-USD/book', auth=auth).json()
    curr_bid = float(curr_data['bids'][0][0])
    text = json.dumps(curr_data, sort_keys=True, indent=4)
    print(text)

    long_flag = True if BTC_BALANCE*curr_bid > CASH_BALANCE else False

    while(True):
        print(long_flag)
        dataframe = getMarketData(BTC_data)

        curr_bid = float(dataframe['Bid Price'].iloc[-1])
        new_cost_basis = ((cost_basis*BTC_BALANCE)+(curr_bid*BTC_BALANCE*FEE_PERCENT))/BTC_BALANCE
        print('CURRENT BID: ', curr_bid)
        print('SELL FEE: ', curr_bid*BTC_BALANCE*FEE_PERCENT)
        print('NEW COST BASIS: ', ((cost_basis*BTC_BALANCE)+(curr_bid*BTC_BALANCE*FEE_PERCENT))/BTC_BALANCE)

        if long_flag == False and dataframe['MACD'].iloc[-1] > dataframe['Signal'].iloc[-1]:
            buy(dataframe)
        elif long_flag == True and dataframe['MACD'].iloc[-1] < dataframe['Signal'].iloc[-1] and curr_bid > new_cost_basis:
            sell(dataframe)

        updateAccountBalances()

        time.sleep(1) # TODO: change to 60 seconds when actually using bot for minute quotes
        print(BTC_data)
        print(dataframe)
        print(dataframe['MACD'].iloc[-1])


bot()
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
