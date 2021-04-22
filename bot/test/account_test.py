from bot.__main__ import api_url
from bot.utils import account

def test_initializeCostBasis1():
    assert account.initializeCostBasis('./utils/mocks/trade_activity_mock1.csv') == 0
    
def test_initializeCostBasis2():
    assert account.initializeCostBasis('./utils/mocks/trade_activity_mock2.csv') == 57836.54409126203

def test_initializeAccountInfo1(requests_mock):
    requests_mock.get(api_url+'accounts',json=[{'currency':'USD','id':'1','available':'2'},{'currency':'BTC','id':'3','available':'4'}])
    assert account.initializeAccountInfo(api_url,{}) == ('1',2,'3',4)

def test_initializeAccountInfo2(requests_mock):
    requests_mock.get(api_url+'accounts',status_code=401)
    assert account.initializeAccountInfo(api_url,{}) == ('',0,'',0)

def test_updateAccountBalances1(requests_mock):
    requests_mock.get(api_url+'accounts',json=[{'currency':'USD','available':'2000'},{'currency':'BTC', 'available':'4'}])
    assert account.updateAccountBalances(api_url,{}) == (2000,4)

def test_updateAccountBalances2(requests_mock):
    requests_mock.get(api_url+'accounts',status_code=401)
    assert account.updateAccountBalances(api_url,{}) == (0,0)

def test_updateFeePercent1():
    assert account.updateFeePercent('./utils/mocks/trade_activity_mock1.csv') == 0.0018

def test_updateFeePercent2():
    assert account.updateFeePercent('./utils/mocks/trade_activity_mock2.csv') == 0.002