import requests, json, hmac, hashlib, time, base64, codecs
from requests.auth import AuthBase
import pandas as pd
from collections import deque
import math
import csv
from datetime import datetime
import os
from dotenv import load_dotenv

from utils import auth, write_files, account, market

load_dotenv()

def truncate(number, digits) -> float:
    stepper = 10.0 ** digits
    return math.trunc(stepper * number) / stepper

API_SECRET = os.environ.get('API_SECRET')
API_KEY = os.environ.get('API_KEY')
API_PASS = os.environ.get('API_PASS')
api_url = 'https://api-public.sandbox.pro.coinbase.com/'
CASH_ACCOUNT = ''
BTC_ACCOUNT = ''
CASH_BALANCE = 0
BTC_BALANCE = 0
FEE_PERCENT = .005
long_flag = False
cost_basis = 0


def buy(dataframe):
    global long_flag, cost_basis, FEE_PERCENT
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
        write_files.recordError('BUY',order.status_code,order.json()['message'])
    time.sleep(1) # allow time for order to fill
    order = requests.get(api_url + 'orders/' + order_id, auth=auth)
    if order.status_code == 200 and order.json()['status'] == 'done':
        print("BUY SUCCEEDED")
        text = json.dumps(order.json(), sort_keys=True, indent=4)
        print (text)
        long_flag = True
        executed_value = float(order.json()['executed_value'])
        fill_size = float(order.json()['size'])
        fill_price = executed_value/fill_size
        fill_fee = float(order.json()['fill_fees'])
        cost_basis = (executed_value+fill_fee)/fill_size
        print('COST BASIS AFTER BUY: ', cost_basis)
        write_files.recordActivity('BUY',fill_price,fill_size,executed_value,fill_fee,cost_basis,0)
        FEE_PERCENT = account.updateFeePercent()
    else:
        delete = requests.delete(api_url + 'orders', auth=auth)
        write_files.recordError('BUY',order.status_code,'CANCELED')

def sell(dataframe):
    global long_flag, FEE_PERCENT
    curr_bid = float(dataframe['Bid Price'].iloc[-1])
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
        write_files.recordError('SELL',order.status_code,order.json()['message'])
    time.sleep(1) # allow time for order to fill
    order = requests.get(api_url + 'orders/' + order_id, auth=auth)
    if order.status_code == 200 and order.json()['status'] == 'done':
        print("SELL SUCCEEDED")
        text = json.dumps(order.json(), sort_keys=True, indent=4)
        print (text)
        long_flag = False
        executed_value = float(order.json()['executed_value'])
        fill_size = float(order.json()['size'])
        fill_price = executed_value/fill_size
        fill_fee = float(order.json()['fill_fees'])
        final_cost_basis = ((cost_basis*fill_size)+fill_fee)/fill_size
        profit = (fill_price-final_cost_basis)*fill_size
        write_files.recordActivity('SELL',fill_price,fill_size,executed_value,fill_fee,final_cost_basis,profit)
        FEE_PERCENT = account.updateFeePercent()
    else:
        delete = requests.delete(api_url + 'orders', auth=auth)
        write_files.recordError('BUY',order.status_code,'CANCELED')

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


auth = auth.CoinbaseAuth(API_KEY, API_SECRET, API_PASS)

order_details = {
        'type': 'limit',
        'side': 'sell',
        'product_id': 'BTC-USD',
        'price': 1, # order limit is current ask price for fast fill 
        'size': 0.01 # max trade size accounting for fee % and maximum size precision
    }
order = requests.post(api_url + 'orders', json=order_details, auth=auth)
print(order.json())
order_id = order.json()['id']
order = requests.get(api_url + 'orders/' + order_id, auth=auth)
print(order.json())

def bot():
    global CASH_ACCOUNT, BTC_ACCOUNT, CASH_BALANCE, BTC_BALANCE, long_flag, cost_basis

    BTC_data = deque(maxlen=200)

    FEE_PERCENT = account.updateFeePercent()
    print(FEE_PERCENT)

    cost_basis = account.initializeCostBasis()
    CASH_ACCOUNT, CASH_BALANCE, BTC_ACCOUNT, BTC_BALANCE = account.initializeAccountInfo(api_url,auth)

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
        dataframe = market.getMarketData(api_url,auth,BTC_data)

        curr_bid = float(dataframe['Bid Price'].iloc[-1])
        new_cost_basis = ((cost_basis*BTC_BALANCE)+(curr_bid*BTC_BALANCE*FEE_PERCENT))/BTC_BALANCE
        print('CURRENT BID: ', curr_bid)
        print('SELL FEE: ', curr_bid*BTC_BALANCE*FEE_PERCENT)
        print('NEW COST BASIS: ', ((cost_basis*BTC_BALANCE)+(curr_bid*BTC_BALANCE*FEE_PERCENT))/BTC_BALANCE)

        if long_flag == False and dataframe['MACD'].iloc[-1] > dataframe['Signal'].iloc[-1]:
            buy(dataframe)
        elif long_flag == True and dataframe['MACD'].iloc[-1] < dataframe['Signal'].iloc[-1] and curr_bid > new_cost_basis:
            sell(dataframe)

        CASH_BALANCE, BTC_BALANCE = account.updateAccountBalances(api_url,auth)

        time.sleep(1) # TODO: change to 60 seconds when actually using bot for minute quotes
        print(BTC_data)
        print(dataframe)
        print(dataframe['MACD'].iloc[-1])


bot()