from bot.utils import market
from bot.__main__ import api_url
import pandas as pd
import numpy as np
from pandas._testing import assert_frame_equal

def test_getMarketData1(requests_mock):
    requests_mock.get(api_url+'products/BTC-USD/book',json={"bids":[["63150.71","3008.75745769",1]],"asks":[["63150.73","3009.48614189",1]],"sequence":310102899}, status_code=200)
    data = pd.read_json('./bot/mocks/dataframe_mock.json')
    dataframe = pd.DataFrame(data)
    market_data = market.getMarketData(api_url,{},[])
    del market_data['Unix Timestamp']
    assert_frame_equal(market_data, dataframe, check_dtype=False)

def test_getMarketData2(requests_mock):
    requests_mock.get(api_url+'products/BTC-USD/book', status_code=401)
    dataframe = pd.DataFrame([{'Unix Timestamp':0, 'Ask Price':0, 'Ask Size':0, 'Bid Price':0, 'Bid Size':0,'Average Price':0,'ShortEMA':0,'LongEMA':0,'MACD':0,'Signal':0}])
    market_data = market.getMarketData(api_url,{},[{'Unix Timestamp':0,'Ask Price':0,'Ask Size':0,'Bid Price':0,'Bid Size':0}])
    assert_frame_equal(market_data,dataframe, check_dtype=False)