import numpy as np 
import pandas as pd
import pandas_ta as ta
import yfinance as yf
import json
from pydantic import Field, BaseModel
from langchain_core.tools import tool

K_PERIOD=14
D_PERIOD=3

class StockTechnicalIndicatorInput(BaseModel):
    ticker: str = Field(description="he stock symbol to get technical indicators and historical data for")

@tool("get_stock_technical_indicators", args_schema=StockTechnicalIndicatorInput)
def get_stock_technical_indicators(ticker: str ) -> str:
    """
    Used for getting the technical indicators and historical data for a stock symbol.
    """
    prices = yf.Ticker(ticker).history(period="6mo")
    
    #Calculate the MACD - Moving Average Convergence Divergence
    prices.ta.macd(close="Close", fast=12, slow=26, signal=9, append=True)
    prices.rename(columns={"MACD_12_26_9": "macd", "MACDs_12_26_9": "macd_signal", "MACDh_12_26_9": "macd_histogram"}, inplace=True)

    #Calculate the Stochastics
    prices["n_high"] = prices["High"].rolling(K_PERIOD).max()
    prices["n_low"] = prices["Low"].rolling(K_PERIOD).min()
    prices["%K"] = (prices["Close"] - prices["n_low"]) * 100 / (prices["n_high"] - prices["n_low"])
    prices["%D"] = prices['%K'].rolling(D_PERIOD).mean()
    
    #Calculate the RSI - Relative Strength Index
    delta = prices["Close"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0) 
    avg_gain = gain.rolling(7).mean()
    avg_loss = loss.rolling(7).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    prices["rsi"] = prices.index.map(rsi)

    #Calculate ADR - Average Daily Range
    prices["dr"] = prices.apply(lambda x: x["High"] - x["Low"], axis=1)
    prices["adr"] = prices["dr"].rolling(7).mean()

    #Reformat the datetimeindex array to be string in the format of YYYY-MM-DD
    prices.index = prices.index.strftime("%Y-%m-%d")

    return json.dumps(prices.groupby(prices.index).agg(list).to_dict(orient="index"), indent=4)
    
    #f"The relative Strength Index (RSI) for {symbol} is {rsi}.   The MACD for {symbol} is {macd} and the MACD Signal is {macd_s}.  The Stochastics for {symbol} is %K: {prices['%K']} and %D: {prices['%D']}"
