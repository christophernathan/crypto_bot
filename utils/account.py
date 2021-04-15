import pandas as pd
import requests, time

def initializeCostBasis(csv_path):
    activity = pd.read_csv(csv_path)
    frame = pd.DataFrame(activity)
    if frame.iloc[-1]['Trade Side'] == 'BUY':
        return frame.iloc[-1]['Cost Basis']
    return 0

def initializeAccountInfo(api_url, auth):
    accounts = requests.get(api_url + 'accounts', auth=auth)
    if accounts.status_code!=200:
        return '',0,'',0
    for account in accounts.json():
        if account.get('currency') == 'USD':
            CASH_ACCOUNT = account.get('id')
            CASH_BALANCE = float(account.get('available'))
        elif account.get('currency') == 'BTC':
            BTC_ACCOUNT = account.get('id')
            BTC_BALANCE = float(account.get('available'))
    return CASH_ACCOUNT, CASH_BALANCE, BTC_ACCOUNT, BTC_BALANCE

def updateAccountBalances(api_url, auth):
    accounts = requests.get(api_url + 'accounts', auth=auth)
    if accounts.status_code!=200:
        return 0,0
    for account in accounts.json():
        if account.get('currency') == 'USD':
            CASH_BALANCE = float(account.get('available'))
        elif account.get('currency') == 'BTC':
            BTC_BALANCE = float(account.get('available'))
    return CASH_BALANCE, BTC_BALANCE

def updateFeePercent(csv_path): # assuming Taker fee classification to be safe. Percents current as of 4/3/21
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
    activity = pd.read_csv(csv_path)
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
            return fee_table[key]
    return fee_table[list(fee_table)[-1]]