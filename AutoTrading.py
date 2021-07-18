# region Imports
from Orders import Orders
from Strategy import BasicStrategy
from Pair import Pair
import json
import time
from datetime import datetime
from decimal import Decimal
from pprint import pp, pprint

import pandas as pd
import pandas_ta as ta
import websocket
from binance_f import RequestClient, SubscriptionClient
from binance_f.base.printobject import *
from binance_f.constant.test import *
from binance_f.model.constant import *
from twisted.internet import reactor

# Change the configExample.py with your API  key and secret. Rename to config.py
import config

# endregion

# region Pandas Config
pd.options.display.max_columns = 100
pd.options.display.float_format = '{:.3f}'.format
# endregion

# Exchenge API
SOCKET = "wss://fstream.binance.com/ws"
INTERVAL = CandlestickInterval.MIN1
request_client = RequestClient(api_key=config.KEY, secret_key=config.SECRET)

# Symbols
symbols = {
    'BTCUSDT': {"leverage": 28, "resource": 2.0},
}

# Indicators
indicators = {
    "StochRSI":{
        "Type": "StochRSI",
        "Params":{
            "rsi_length":14,
            "length":14,
            "k": 3,
            "d": 3,
            "col_names": ("StochRSI_D", "StochRSI_K")
        }
    },
    "EMA_8":{
        "Type": "EMA",
        "Params":{
            "length":8
        }
    },
    "EMA_200":{
        "Type": "EMA",
        "Params":{
            "length":200
        }
    },
    "MACD":{
        "Type": "MACD",
        "Params":{
            "fast": 12, 
            "slow": 26, 
            "signal": 9,
            "col_names": ("MACD", "MACD_H", "MACD_S")
        }
    },
    "ATR":{
        "Type": "ATR",
        "Params":{
            "length":14, 
            "mamode": "rma"
        }
    },
}

# Pairs for trade
pairs = {}

# Orders functions
orders = Orders(request_client=request_client)

# Strategy
strategy = BasicStrategy(orders=orders)

# Account Balance
balance = 0.0

# Balance Update
def updateBalance():
    global balance
    balance = request_client.get_balance_v2()
    for b in balance:
        if b.asset == 'USDT':
            balance = b.availableBalance
            print("\n- Balance: "+str(balance))
            break


# Open websocket
def onOpenSocket(ws: websocket):
    global INTERVAL
    print('\n-------------- Open --------------\n')

    subscribe = {
        "id": 1,
        "method": "SUBSCRIBE",
        "params": []
    }

    listen_key = request_client.start_user_data_stream()
    subscribe['params'].append(listen_key)
    ws.send(json.dumps(subscribe))

    for pair in pairs:
        while True:
            historical = request_client.get_candlestick_data(symbol = pair, interval = INTERVAL,  startTime=None, endTime=None, limit=200)
            if (int(request_client.get_servertime()) - int(historical[len(historical)-1].closeTime)) > 240000: #240000 = 4min
                time.sleep(60)
                continue
            for index in range(len(historical)-1):
                data = historical[index]
                pairs[pair].addValue({
                        "Symbol": pair, 
                        "time": data.closeTime, 
                        "KLineStart": data.openTime, 
                        "KLineClose": data.closeTime, 
                        "Interval": INTERVAL, 
                        "OpenPrice": float(data.open), 
                        "ClosePrice": float(data.close), 
                        "HighPrice": float(data.high), 
                        "LowPrice": float(data.low),
                        "NumberOfTrades": data.numTrades, 
                        "IsKLineClose": True, 
                        "QuoteAssetVolume": float(data.quoteAssetVolume), 
                        "TakerBuyBaseAssetVolume": float(data.takerBuyBaseAssetVolume), 
                        "TakerBuyQuoteAssetVolume": float(data.takerBuyQuoteAssetVolume)
                    })
            break
        
        subscribe['id'] = subscribe['id'] + 1
        subscribe["params"] = [pair.lower()+"@kline_"+INTERVAL]
        ws.send(json.dumps(subscribe))
        print("Subscribe: "+pair)


# Close websocket
def onCloseSocket(ws):
    print('\n-------------- Close --------------\n')
    # for pair in pairs:
    #     print(pairs[pair].values)
    #     print(pairs[pair].__dict__)


# Receive websocket data
def onReceiveData(ws, message):
    try:
        msg = json.loads(message)

        if not ('e' in msg.keys()) or msg['e'] != 'kline':
            return

        msgData = msg['k']

        if msgData['x'] == True: #Change!
            print("\nSymbol: "+msgData['s']+"   ClosePrice: "+msgData['c'])
            pairs[msg['s']].addValue(
                {
                    "Symbol": msgData['s'], 
                    "time": msg['E'], 
                    "KLineStart": msgData['t'], 
                    "KLineClose": msgData['T'], 
                    "Interval": msgData['i'], 
                    "FirstTradeID": msgData['f'], 
                    "LastTradeID": msgData['L'], 
                    "OpenPrice": float(msgData['o']), 
                    "ClosePrice": float(msgData['c']), 
                    "HighPrice": float(msgData['h']), 
                    "LowPrice": float(msgData['l']), 
                    "BaseAssetVolume": float(msgData['v']), 
                    "NumberOfTrades": msgData['n'], 
                    "IsKLineClose": msgData['x'], 
                    "QuoteAssetVolume": float(msgData['q']), 
                    "TakerBuyBaseAssetVolume": float(msgData['V']), 
                    "TakerBuyQuoteAssetVolume": float(msgData['Q'])
                })
            
            strategy.execute(pair=pairs[msg['s']], balance=balance)

    except Exception as e:        
        if e.args[0] == 'e':
            print("WebSocket Message received")
        pprint(e)


# Load pairs infos
symbolsInf = request_client.get_exchange_information().symbols
keys = symbols.keys()

print("\n- Pairs:")
for symbolInf in symbolsInf:
    if symbolInf.symbol in keys:
        minQty = 0
        for f in symbolInf.filters:
            if f['filterType'] == 'LOT_SIZE':
                minQty = f['minQty']
                break

        pairs[symbolInf.symbol] = Pair(symbol=symbolInf.symbol.lower(), baseToken=symbolInf.quoteAsset, pairToken=symbolInf.baseAsset, pricePrecision=symbolInf.pricePrecision, quantityPrecision=symbolInf.quantityPrecision, minQuantity=minQty, indicators=indicators)
        print("  - "+symbolInf.baseAsset+'/'+symbolInf.quoteAsset)
        
    if len(pairs) >= len(keys):
        break

# Load balance
updateBalance()

# Start
ws = websocket.WebSocketApp(SOCKET, on_open=onOpenSocket, on_close=onCloseSocket, on_message=onReceiveData)
ws.run_forever()
