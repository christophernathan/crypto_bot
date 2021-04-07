import pandas as pd

def initializeCostBasis():
    activity = pd.read_csv('../trade_activity.csv')
    frame = pd.DataFrame(activity)
    if frame.iloc[-1]['Trade Side'] == 'BUY':
        return frame.iloc[-1]['Cost Basis']
    