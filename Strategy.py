from decimal import Decimal
from pprint import pprint

import pandas as pd

from Pair import *
import Actions


class Strategy:
    orders = None
    
    def __init__(self, orders: Actions):
        self.orders = orders
    
    def execute(self, pair: Pair, balance):
        print("Execution")


class BasicStrategy(Strategy):
    
    def execute(self, pair: Pair, balance):
        if not pair.active:
            return
        
        pair.applyIndicator('EMA_8')
        pair.applyIndicator('EMA_200')
        pair.applyIndicator('StochRSI')
        pair.applyIndicator('MACD')
        
        candle = pair.values.iloc[-1]
        previous = pair.values.iloc[-2]


        if (candle['ClosePrice'] > candle['EMA_200'] and previous['MACD_H'] < 0 and previous["MACD_H"] < candle["MACD_H"] and previous["StochRSI_K"] < 20 and candle["StochRSI_K"] > previous["StochRSI_K"]):
            pair.applyIndicator('ATR')
            candle = pair.values.iloc[-1]
            stop = format(float(candle['LowPrice']) - float(candle['ATRr_14']),'.'+str(pair.pricePrecision)+'f')
            take = format(float(candle['HighPrice']) + float(candle['ATRr_14']),'.'+str(pair.pricePrecision)+'f')
            self.orders.newAlert(stop=stop, take=take)
            pair.active = False


class EMA8Strategy(Strategy):
    
    def execute(self, pair: Pair, balance):
        if not pair.active:
            return
        
        pair.applyIndicator('EMA_8')
        
        candle = pair.values.iloc[-1]
        previous = pair.values.iloc[-2]

        if (candle['ClosePrice'] > candle['EMA_8']):
            pair.applyIndicator('ATR')
            candle = pair.values.iloc[-1]
            stop = format(float(candle['LowPrice']) - float(candle['ATRr_14']),'.'+str(pair.pricePrecision)+'f')
            take = format(float(candle['HighPrice']) + float(candle['ATRr_14']),'.'+str(pair.pricePrecision)+'f')
            self.orders.newAlert(stop=stop, take=take)
            pair.active = False

