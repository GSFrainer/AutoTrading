import Strategy


baseCurrency = "USDT"

symbols = {
    'BTCUSDT': {"leverage": 28, "resource": 2.0, "strategy": Strategy.EMA8Strategy},
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