import requests, json, hmac, hashlib, time, base64, codecs, math, csv, os, sys
from requests.auth import AuthBase
import pandas as pd
from collections import deque
from datetime import datetime
from dotenv import load_dotenv

from bot.utils import authentication, write_files, account, market, formatting, trade

load_dotenv()

API_SECRET = os.environ.get('API_SECRET')
API_KEY = os.environ.get('API_KEY')
API_PASS = os.environ.get('API_PASS')
api_url = 'https://api-public.sandbox.pro.coinbase.com/'

def bot():
    auth = authentication.CoinbaseAuth(API_KEY, API_SECRET, API_PASS)

    BTC_data = deque(maxlen=200)

    FEE_PERCENT = account.updateFeePercent('trade_activity.csv')
    print(FEE_PERCENT)

    cost_basis = account.initializeCostBasis('trade_activity.csv')
    CASH_ACCOUNT, CASH_BALANCE, BTC_ACCOUNT, BTC_BALANCE = account.initializeAccountInfo(api_url,auth)
    cost_basis=0 # temporary to force sell

    print(CASH_ACCOUNT)
    print(CASH_BALANCE)
    print(BTC_ACCOUNT)
    print(BTC_BALANCE)

    curr_data = requests.get(api_url + 'products/BTC-USD/book', auth=auth).json()
    curr_bid = float(curr_data.get('bids')[0][0])
    text = json.dumps(curr_data, sort_keys=True, indent=4)
    print(text)

    long_flag = True if BTC_BALANCE*curr_bid > CASH_BALANCE else False

    while(True):
        print(long_flag)
        dataframe = market.getMarketData(api_url,auth,BTC_data)

        curr_bid = float(dataframe['Bid Price'].iloc[-1])
        print('cost_basis: ', type(cost_basis))
        print('BTC BALANCE: ', type(BTC_BALANCE))
        print('curr_bid: ', type(curr_bid))
        print('FEE PERCENT: ', type(FEE_PERCENT))
        new_cost_basis = ((cost_basis*BTC_BALANCE)+(curr_bid*BTC_BALANCE*FEE_PERCENT))/BTC_BALANCE
        print('CURRENT BID: ', curr_bid)
        print('SELL FEE: ', curr_bid*BTC_BALANCE*FEE_PERCENT)
        print('NEW COST BASIS: ', ((cost_basis*BTC_BALANCE)+(curr_bid*BTC_BALANCE*FEE_PERCENT))/BTC_BALANCE)

        if long_flag == False and dataframe['MACD'].iloc[-1] > dataframe['Signal'].iloc[-1]:
            long_flag, cost_basis, FEE_PERCENT = trade.buy(api_url,auth,dataframe,FEE_PERCENT,CASH_BALANCE)
            print(long_flag)
        elif long_flag == True and dataframe['MACD'].iloc[-1] < dataframe['Signal'].iloc[-1] and curr_bid > new_cost_basis:
            long_flag, cost_basis, FEE_PERCENT = trade.sell(api_url,auth,dataframe,cost_basis,BTC_BALANCE,FEE_PERCENT)
            print(long_flag)

        CASH_BALANCE, BTC_BALANCE = account.updateAccountBalances(api_url,auth)

        time.sleep(1) # TODO: change to 60 seconds when actually using bot for minute quotes
        print(BTC_data)
        print(dataframe)
        print(dataframe['MACD'].iloc[-1])

if __name__ == "__main__":
    bot()