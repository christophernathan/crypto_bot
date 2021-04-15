from utils import market
from bot import api_url

def test_getMarketData(requests_mock):
    requests_mock.get(api_url+'products/BTC-USD/book',json={"bids":[["63150.71","3008.75745769",1]],"asks":[["63150.73","3009.48614189",1]],"sequence":310102899})
    print(market.getMarketData(api_url,{},[]))# == ['1','1','1','1','1','1','1','1','1','1']