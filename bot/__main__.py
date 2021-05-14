import requests, time, os, sys
from collections import deque
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from bot.utils import authentication, account, market, trade

load_dotenv()

API_SECRET = os.environ.get('API_SECRET')
API_KEY = os.environ.get('API_KEY')
API_PASS = os.environ.get('API_PASS')
api_url = 'https://api-public.sandbox.pro.coinbase.com/'

def bot():
    print("==== BEGINNING TRADING ====")
    print("===========================")
    auth = authentication.CoinbaseAuth(API_KEY, API_SECRET, API_PASS)

    BTC_data = deque(maxlen=200)

    FEE_PERCENT = account.updateFeePercent('trade_activity.csv')
    print("Current Trading Fee Percent: ", FEE_PERCENT)

    cost_basis = account.initializeCostBasis('trade_activity.csv')
    CASH_ACCOUNT, CASH_BALANCE, BTC_ACCOUNT, BTC_BALANCE = account.initializeAccountInfo(api_url,auth)
    print("Current USD Balance: ", CASH_BALANCE)
    print("Current BTC Balance: ", BTC_BALANCE,"\n")

    curr_data = requests.get(api_url + 'products/BTC-USD/book', auth=auth).json()
    curr_bid = float(curr_data.get('bids')[0][0])

    long_flag = True if BTC_BALANCE*curr_bid > CASH_BALANCE else False

    while(True):
        dataframe = market.getMarketData(api_url,auth,BTC_data)

        curr_bid = float(dataframe['Bid Price'].iloc[-1])
        new_cost_basis = ((cost_basis*BTC_BALANCE)+(curr_bid*BTC_BALANCE*FEE_PERCENT))/BTC_BALANCE

        if long_flag == False and dataframe['MACD'].iloc[-1] > dataframe['Signal'].iloc[-1]:
            long_flag, cost_basis, FEE_PERCENT = trade.buy(api_url,auth,dataframe,FEE_PERCENT,CASH_BALANCE)
            account.printUpdatedInfo(api_url,auth,FEE_PERCENT)
        elif long_flag == True and dataframe['MACD'].iloc[-1] < dataframe['Signal'].iloc[-1] and curr_bid > new_cost_basis:
            long_flag, cost_basis, FEE_PERCENT = trade.sell(api_url,auth,dataframe,cost_basis,BTC_BALANCE,FEE_PERCENT)
            account.printUpdatedInfo(api_url,auth,FEE_PERCENT)


        time.sleep(1)
        print(BTC_data)
        print(dataframe)