import requests, time, json
from utils import formatting, write_files, account

def buy(api_url, auth, dataframe, long_flag, FEE_PERCENT, cost_basis, CASH_BALANCE):
    global long_flag, cost_basis, FEE_PERCENT
    print(dataframe)
    curr_ask = float(dataframe['Ask Price'].iloc[-1])
    max_order_size = min(float(CASH_BALANCE),10000*curr_ask)
    effective_order_size = formatting.truncate(max_order_size/(curr_ask*(1+FEE_PERCENT)),8)
    print(CASH_BALANCE)
    print(min(float(CASH_BALANCE),10000))
    print(curr_ask)
    print(float(dataframe['Ask Price'].iloc[-1]))
    print(min(float(CASH_BALANCE),10000*curr_ask)/curr_ask)
    order_details = {
        'type': 'limit',
        'side': 'buy',
        'product_id': 'BTC-USD',
        'price': curr_ask, # order limit is current ask price for fast fill 
        'size': effective_order_size # max trade size accounting for fee % and maximum size precision
    }
    order = requests.post(api_url + 'orders', json=order_details, auth=auth)
    order_id = order.json()['id']
    if order.status_code != 200:
        write_files.recordError('trade_errors.csv','BUY',order.status_code,order.json()['message'])
    time.sleep(1) # allow time for order to fill
    order = requests.get(api_url + 'orders/' + order_id, auth=auth)
    if order.status_code == 200 and order.json()['status'] == 'done':
        print("BUY SUCCEEDED")
        text = json.dumps(order.json(), sort_keys=True, indent=4)
        print (text)
        long_flag = True
        executed_value = float(order.json()['executed_value'])
        fill_size = float(order.json()['size'])
        fill_price = executed_value/fill_size
        fill_fee = float(order.json()['fill_fees'])
        cost_basis = (executed_value+fill_fee)/fill_size
        print('COST BASIS AFTER BUY: ', cost_basis)
        write_files.recordActivity('trade_activity.csv','BUY',fill_price,fill_size,executed_value,fill_fee,cost_basis,0)
        FEE_PERCENT = account.updateFeePercent('trade_activity.csv')
    else:
        delete = requests.delete(api_url + 'orders', auth=auth)
        write_files.recordError('trade_errors.csv','BUY',order.status_code,'CANCELED')