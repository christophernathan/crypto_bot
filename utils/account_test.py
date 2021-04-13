from utils import account, mocks

def test_initializeCostBasis1():
    assert account.initializeCostBasis('./utils/mocks/trade_activity_mock1.csv') == 0

def test_initializeCostBasis2():
    assert account.initializeCostBasis('./utils/mocks/trade_activity_mock2.csv') == 57836.54409126203

