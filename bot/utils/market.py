import requests, time
import pandas as pd

def getMarketData(api_url, auth, BTC_data):
    curr_data = requests.get(api_url + 'products/BTC-USD/book', auth=auth)
    if curr_data.status_code==200:
        curr_data = curr_data.json()
        BTC_data.append([time.time(),float(curr_data.get('asks')[0][0]),float(curr_data.get('asks')[0][1]),float(curr_data.get('bids')[0][0]),float(curr_data.get('bids')[0][1])])
    dataframe = pd.DataFrame(BTC_data)
    dataframe.columns = ['Unix Timestamp', 'Ask Price', 'Ask Size', 'Bid Price', 'Bid Size']
    dataframe['Average Price'] = dataframe.apply(lambda row: (row['Ask Price']+row['Bid Price'])/2, axis=1)
    ShortEMA = dataframe['Average Price'].ewm(span=12,adjust=False).mean()
    LongEMA = dataframe['Average Price'].ewm(span=26,adjust=False).mean()
    MACD = ShortEMA - LongEMA
    signal = MACD.ewm(span=9,adjust=False).mean()
    dataframe['ShortEMA'] = ShortEMA
    dataframe['LongEMA'] = LongEMA
    dataframe['MACD'] = MACD
    dataframe['Signal'] = signal
    return dataframe