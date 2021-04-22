import requests, time, json
from bot.utils import formatting, write_files, account

def buy(api_url, auth, dataframe, FEE_PERCENT, CASH_BALANCE):
    print("Attempting To Buy BTC")
    curr_ask = float(dataframe['Ask Price'].iloc[-1])
    max_order_size = min(float(CASH_BALANCE),10000*curr_ask)
    effective_order_size = formatting.truncate(max_order_size/(curr_ask*(1+FEE_PERCENT)),8)
    order_details = {
        'type': 'limit',
        'side': 'buy',
        'product_id': 'BTC-USD',
        'price': curr_ask, # order limit is current ask price for fast fill 
        'size': effective_order_size # max trade size accounting for fee % and maximum size precision
    }
    print("Attempting to buy %f BTC at $%f per BTC" %(effective_order_size,curr_ask))
    order = requests.post(api_url + 'orders', json=order_details, auth=auth)
    order_id = order.json().get('id')
    if order.status_code != 200:
        print("Buy order was rejected: %s\n" %order.json().get('message'))
        write_files.recordError('trade_errors.csv','BUY',order.status_code,order.json().get('message'))
        return False,0,FEE_PERCENT
    time.sleep(1) # allow time for order to fill
    order = requests.get(api_url + 'orders/' + order_id, auth=auth)
    if order.status_code == 200 and order.json().get('status') == 'done':
        executed_value = float(order.json().get('executed_value'))
        fill_size = float(order.json().get('size'))
        fill_price = executed_value/fill_size
        fill_fee = float(order.json().get('fill_fees'))
        cost_basis = (executed_value+fill_fee)/fill_size
        print("BUY SUCCEEDED")
        print("Bought %f BTC at $%f per BTC for a fee of $%f\n" %(fill_size,fill_price,fill_fee))
        write_files.recordActivity('trade_activity.csv','BUY',fill_price,fill_size,executed_value,fill_fee,cost_basis,0)
        FEE_PERCENT = account.updateFeePercent('trade_activity.csv')
        return True,cost_basis,FEE_PERCENT
    else:
        delete = requests.delete(api_url + 'orders', auth=auth)
        print("Buy order was canceled\n")
        write_files.recordError('trade_errors.csv','BUY',order.status_code,'CANCELED')
        return False,0,FEE_PERCENT

def sell(api_url, auth, dataframe, cost_basis, BTC_BALANCE, FEE_PERCENT):
    print("Attempting To Sell BTC")
    curr_bid = float(dataframe['Bid Price'].iloc[-1])
    max_order_size = min(float(BTC_BALANCE),10000)
    effective_order_size = formatting.truncate(max_order_size/(1+FEE_PERCENT),8)
    order_details = {
        'type': 'limit',
        'side': 'sell',
        'product_id': 'BTC-USD',
        'price': curr_bid, # order limit is current ask price for fast fill 
        'size': effective_order_size # max trade size accounting for fee % and maximum size precision
    }
    print("Attempting to sell %f BTC at $%f per BTC" %(effective_order_size,curr_bid))
    order = requests.post(api_url + 'orders', json=order_details, auth=auth)
    order_id = order.json().get('id')
    if order.status_code != 200:
        print("Sell order was rejected: %s\n" %order.json().get('message'))
        write_files.recordError('trade_errors.csv','SELL',order.status_code,order.json().get('message'))
        return True,cost_basis,FEE_PERCENT
    time.sleep(1) # allow time for order to fill
    order = requests.get(api_url + 'orders/' + order_id, auth=auth)
    if order.status_code == 200 and order.json().get('status') == 'done':
        executed_value = float(order.json().get('executed_value'))
        fill_size = float(order.json().get('size'))
        fill_price = executed_value/fill_size
        fill_fee = float(order.json().get('fill_fees'))
        final_cost_basis = ((cost_basis*fill_size)+fill_fee)/fill_size
        profit = (fill_price-final_cost_basis)*fill_size
        print("SELL SUCCEEDED")
        print("Sold %f BTC at $%f per BTC for a fee of $%f\n" %(fill_size,fill_price,fill_fee))
        write_files.recordActivity('trade_activity.csv','SELL',fill_price,fill_size,executed_value,fill_fee,final_cost_basis,profit)
        FEE_PERCENT = account.updateFeePercent('trade_activity.csv')
        return False,cost_basis,FEE_PERCENT
    else:
        delete = requests.delete(api_url + 'orders', auth=auth)
        print("Sell order was canceled\n")
        write_files.recordError('trade_errors.csv','BUY',order.status_code,'CANCELED')
        return True,cost_basis,FEE_PERCENT