import pandas as pd
import pandas_ta as ta

from pprint import pprint


#Consts
#Maximum length of values dataframe
MAX_VALUES_LEN = 2000
#Length to reshape the dataframe
VALUES_SLICE_LEN = 1600


class Pair:

    symbol = ''
    baseToken = ''
    pairToken = ''

    pricePrecision = 0
    quantityPrecision = 0
    minQuantity = 0

    values = None
    indicators = None
    strategy = None

    active = True

    def __init__(self, symbol, baseToken, pairToken, pricePrecision, quantityPrecision, minQuantity, indicators, strategy):
        self.symbol = symbol
        self.baseToken = baseToken
        self.pairToken = pairToken
        
        self.pricePrecision = pricePrecision
        self.quantityPrecision = quantityPrecision
        self.minQuantity = float(minQuantity)

        self.values = pd.DataFrame({"Symbol": [], "time": [], "KLineStart": [], "KLineClose": [], "Interval": [], "FirstTradeID": [], "LastTradeID": [], "OpenPrice": [], "ClosePrice": [], "HighPrice": [], "LowPrice": [], "BaseAssetVolume": [], "NumberOfTrades": [], "IsKLineClose": [], "QuoteAssetVolume": [], "TakerBuyBaseAssetVolume": [], "TakerBuyQuoteAssetVolume": []})
        self.values = self.values.astype({"time": 'int64', "KLineStart": 'int64', "KLineClose": 'int64', "FirstTradeID": 'int64', "LastTradeID": 'int64', "NumberOfTrades": 'int64', "IsKLineClose": 'boolean'}, copy=False)

        self.indicators = indicators
        self.strategy = strategy

    
    def addValue(self, data):
        self.values = self.values.append(data, ignore_index=True)
        if self.values.shape[0] > MAX_VALUES_LEN:
            self.values = self.values.iloc[VALUES_SLICE_LEN:]

    def applyIndicator(self, indicator):
        if self.indicators[indicator]['Type'].lower() in dir(self.values.ta):
            getattr(self.values.ta, self.indicators[indicator]['Type'].lower())(close = self.values['ClosePrice'], append=True, **self.indicators[indicator]['Params'])
