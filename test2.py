import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
plt.style.use('fivethirtyeight')

data = pd.read_csv('gemini_BTCUSD_2020_1min (1).csv')
data = data.set_index(pd.DatetimeIndex(data['Date'].values))
data = data.iloc[::-1]
print(data)

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


portfolioVal = 1
avgCost = 0
currShares = 0
shareVal = 0

def buy_sell_function(data):
    global portfolioVal
    global avgCost
    global currShares
    global shareVal
    print("PORTFOLIO: ", portfolioVal)
    buy_list = []
    sell_list = []
    flag_long = 0
    for i in range(0,len(data)):
        if data['MACD'][i] > data['Signal'][i] and flag_long==0:
            buy_list.append(data['Close'][i])
            sell_list.append(np.nan)

            newShares = (portfolioVal*4/5)/data['Close'][i]
            currShares += newShares
            shareVal += portfolioVal*4/5
            avgCost = shareVal/currShares
            portfolioVal/=5
            portfolioVal*=4
            #print("Buying ", newShares, " shares. Avg cost: ", avgCost, " New portfolio value: ", portfolioVal)

            flag_long=1
        elif flag_long == 1 and data['MACD'][i] < data['Signal'][i] and data['Close'][i] > avgCost:
            sell_list.append(data['Close'][i])
            buy_list.append(np.nan)

            portfolioVal += currShares*data['Close'][i]
            #print("Current shares ", currShares, " shares. Total value: ", currShares*data['Close'][i], " New portfolio value: ", portfolioVal)
            shareVal=0
            currShares=0

            flag_long = 0
        elif flag_long == 1 and data['MACD'][i] < data['Signal'][i]:
            buy_list.append(np.nan)
            sell_list.append(np.nan)
            flag_long=0
        else:
            buy_list.append(np.nan)
            sell_list.append(np.nan)
    #print(portfolioVal)
    return (buy_list, sell_list)

buySellData = buy_sell_function(data)
data['Buy'] = buySellData[0]
data['Sell'] = buySellData[1]

profit=0
loss=0
pc=1


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

#print(profit)
#print(loss)
#print(pc)
print(portfolioVal + currShares*data['Close'][len(data)-1])