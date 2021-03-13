import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import requests
plt.style.use('fivethirtyeight')

data = pd.read_csv('gemini_BTCUSD_2020_1min (1).csv')
data = data.set_index(pd.DatetimeIndex(data['Date'].values))
data = data.iloc[::-1]
#print(data)

#for i in range(0,len(data)):
#    print(data['Date'][i])


ShortEMA = data.Close.ewm(span=12,adjust=False).mean()
LongEMA = data.Close.ewm(span=26,adjust=False).mean()
MACD = ShortEMA - LongEMA
signal = MACD.ewm(span=9,adjust=False).mean()

data['ShortEMA'] = ShortEMA
data['LongEMA'] = LongEMA
data['MACD'] = MACD
data['Signal'] = signal


def buy_sell_function(data):
    buy_list = []
    sell_list = []
    flag_long = False
    currLong = 0
    for i in range(0,len(data)):
        #print(data['Date'][i])
        if data['MACD'][i] > data['Signal'][i] and flag_long == False:
            buy_list.append(data['Close'][i])
            sell_list.append(np.nan)
            flag_long = True
            currLong = data['Close'][i]
        elif flag_long == True and data['MACD'][i] < data['Signal'][i] and data['Close'][i] > currLong:
            sell_list.append(data['Close'][i])
            buy_list.append(np.nan)
            flag_long = False
        else:
            buy_list.append(np.nan)
            sell_list.append(np.nan)
    return (buy_list, sell_list)

data['Buy'] = buy_sell_function(data)[0]
data['Sell'] = buy_sell_function(data)[1]

profit=0
loss=0
pc=1

currLong = 0

for i in range(0,len(data)):
    #print(data['Sell'][i])
    if not np.isnan(data['Buy'][i]):
        #print("YUH")
        currLong = data['Buy'][i]
    elif not np.isnan(data['Sell'][i]):
        #print("YEET")
        if data['Sell'][i]>=currLong:
            profit += data['Sell'][i] - currLong
            pcGain = 1 + (data['Sell'][i]-currLong)/currLong
            #print(pcGain)
            pc*=pcGain
        else:
            loss += currLong - data['Sell'][i]

#for i in reversed(range(0,len(data))):
 #   print(data['Date'][i], " ", data['Close'][i], " ", data['ShortEMA'][i], " ", data['LongEMA'][i], " ", data['MACD'][i], " ", data['Signal'][i])
        

plt.figure(figsize=(16,8)) #width = 12.2in, height = 4.5
plt.scatter(data.index, data['Buy'], color = 'green', label='Buy Signal', marker = '^', alpha = 1)
plt.scatter(data.index, data['Sell'], color = 'red', label='Sell Signal', marker = 'v', alpha = 1)
#plt.plot(ShortEMA, label='Short/Fast EMA', color = 'red', alpha = 0.35)
#plt.plot(LongEMA, label='Long/Slow EMA', color = 'green', alpha = 0.35)
plt.plot( data['Close'],  label='Close Price', alpha = 0.35)#plt.plot( X-Axis , Y-Axis, line_width, alpha_for_blending,  label)
plt.plot(data.index,MACD+44800,label='BTCUSD MACD',color='blue')
plt.plot(data.index, signal+44800, label='Signal Line', color='orange')

plt.xticks(rotation=45)
#plt.title('Close Price History Buy / Sell Signals')
plt.xlabel('Date',fontsize=18)
plt.ylabel('Close Price USD ($)',fontsize=18)
plt.legend( loc='upper left')
plt.show()

print(profit)
print(loss)
print(pc)