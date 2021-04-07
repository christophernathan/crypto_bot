from datetime import datetime
import time, csv

def recordActivity(side,price,btc_quantity,usd_value,fees,cost_basis,profit):
    with open('../trade_activity.csv', mode='a') as trade_activity:
        record_activity = csv.writer(trade_activity, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        timestamp = int(time.time())
        dateTime = datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        record_activity.writerow([timestamp,dateTime,side,price,btc_quantity,usd_value,fees,cost_basis,profit])

def recordError(side,status_code,reason):
    with open('../trade_errors.csv', mode='a') as trade_errors:
        record_error = csv.writer(trade_errors, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        timestamp = int(time.time())
        dateTime = datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        record_error.writerow([timestamp,dateTime,side,status_code,reason])