from utils import market
from bot import api_url
import pandas as pd
from pandas._testing import assert_frame_equal

def test_getMarketData(requests_mock):
    requests_mock.get(api_url+'products/BTC-USD/book',json={"bids":[["63150.71","3008.75745769",1]],"asks":[["63150.73","3009.48614189",1]],"sequence":310102899})
    data = pd.read_json('./utils/mocks/dataframe_mock.json')
    dataframe = pd.DataFrame(data)
    print()
    print(market.getMarketData(api_url,{},[]))
    print(dataframe)
    print(market.getMarketData(api_url,{},[]).equals(dataframe))
    market_data = market.getMarketData(api_url,{},[])
    del market_data['Unix Timestamp']
    assert_frame_equal(market_data, dataframe, check_dtype=False)