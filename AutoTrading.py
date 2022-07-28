# region Imports
from Actions import Orders
import Strategy
from Pair import Pair

import json
import time
from datetime import datetime
from decimal import Decimal
from pprint import pp, pprint

import pandas as pd
import pandas_ta as ta
import websocket

# region Import Binance 
from binance_f import RequestClient, SubscriptionClient
from binance_f.base.printobject import *
from binance_f.constant.test import *
from binance_f.model.constant import *
from twisted.internet import reactor
# endregion

# Change the AccessExample.py with your API  key and secret. Rename to access.py
import Access
import TradeConfig

# endregion

# region Pandas Config
pd.options.display.max_columns = 100
pd.options.display.float_format = '{:.3f}'.format
# endregion

# Exchenge API
SOCKET = "wss://fstream.binance.com/ws"
INTERVAL = CandlestickInterval.MIN1
request_client = RequestClient(api_key=Access.KEY, secret_key=Access.SECRET)


# Symbols
symbols = TradeConfig.symbols

# Indicators
indicators = TradeConfig.indicators

# Pairs for trade
pairs = {}

# Orders functions
orders = Orders(request_client=request_client)

# Account Balance
balance = 0.0

# Balance Update
def updateBalance():
    global balance
    balance = request_client.get_balance_v2()
    for b in balance:
        if b.asset == TradeConfig.baseCurrency:
            balance = b.availableBalance
            print("\n- Balance: "+str(balance)+" "+TradeConfig.baseCurrency)
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


# Receive websocket data
def onReceiveData(ws, message):
    try:
        msg = json.loads(message)

        if not ('e' in msg.keys()) or msg['e'] != 'kline':
            return

        msgData = msg['k']

        if msgData['x'] == True: #True = Close Candle / False = Every Candle
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
            
            pairs[msg['s']].strategy.execute(pair=pairs[msg['s']], balance=balance)

    except Exception as e:        
        if e.args[0] == 'e':
            print("WebSocket Message received")
        pprint(e)





# Load pairs infos
symbolsInf = request_client.get_exchange_information().symbols
keys = symbols.keys()

print("\n- Pairs:")
try:
    for symbolInf in symbolsInf:
        if symbolInf.symbol in keys:
            minQty = 0
            for f in symbolInf.filters:
                if f['filterType'] == 'LOT_SIZE':
                    minQty = f['minQty']
                    break

            pairStrategy = symbols[symbolInf.symbol]["strategy"](orders=orders)

            if not issubclass(type(pairStrategy), Strategy.Strategy):
                raise Exception("Invalid strategy")
            
            pairs[symbolInf.symbol] = Pair(symbol=symbolInf.symbol.lower(), baseToken=symbolInf.quoteAsset, pairToken=symbolInf.baseAsset, pricePrecision=symbolInf.pricePrecision, quantityPrecision=symbolInf.quantityPrecision, minQuantity=minQty, indicators=indicators, strategy=pairStrategy)
            print("  - "+symbolInf.baseAsset+'/'+symbolInf.quoteAsset+" ("+type(pairStrategy).__name__+")")
            
        if len(pairs) >= len(keys):
            break

except Exception as PairError:
    if len(PairError.args) > 0:
        print(PairError)
    else:
        print("Invalid symbol params")
    sys.exit()


# Load balance
updateBalance()

# Start
ws = websocket.WebSocketApp(SOCKET, on_open=onOpenSocket, on_close=onCloseSocket, on_message=onReceiveData)
ws.run_forever()
