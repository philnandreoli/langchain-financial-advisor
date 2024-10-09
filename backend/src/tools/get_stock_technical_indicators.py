import numpy as np 
import pandas as pd
import pandas_ta as ta
import yfinance as yf
from pydantic import Field, BaseModel
from langchain_core.tools import tool
from typing import List

K_PERIOD=14
D_PERIOD=3

class StockTechnicalIndicatorInput(BaseModel):
    ticker: str = Field(description="he stock symbol to get technical indicators and historical data for")

class StockTechnicalIndicatorOutput(BaseModel):
    date: str = Field(description="The date of the stock data")
    open: float = Field(description="The opening price of the stock")
    high: float = Field(description="The highest price of the stock")
    low: float = Field(description="The lowest price of the stock")
    close: float = Field(description="The closing price of the stock")
    volume: int = Field(description="The volume of the stock")
    macd: float = Field(description="The MACD value")
    macd_histogram: float = Field(description="The MACD Histogram value")
    macd_signal: float = Field(description="The MACD Signal value")
    n_high: float = Field(description="The highest price in the last 14 days")
    n_low: float = Field(description="The lowest price in the last 14 days")
    K: float = Field(description="The %K value for the Stochastics")
    D: float = Field(description="The %D value for the Stochastics")
    rsi: float = Field(description="The Relative Strength Index value")
    dr: float = Field(description="The daily range of the stock")
    adr: float = Field(description="The average daily range of the stock")

@tool("get_stock_technical_indicators", args_schema=StockTechnicalIndicatorInput)
def get_stock_technical_indicators(ticker: str ) -> List[StockTechnicalIndicatorOutput]:
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
    prices["K"] = (prices["Close"] - prices["n_low"]) * 100 / (prices["n_high"] - prices["n_low"])
    prices["D"] = prices['K'].rolling(D_PERIOD).mean()
    
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
    prices.drop(columns=["Dividends", "Stock Splits"], axis=1, inplace=True)
    prices.rename(columns={"Date": "date", "Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"}, inplace=True)
    prices.rename_axis("date", inplace=True)

    stock_technical_indicators = prices.reset_index().to_dict(orient='records')

    technical_indicators: List[StockTechnicalIndicatorOutput] = [StockTechnicalIndicatorOutput(**item) for item in stock_technical_indicators]

    return technical_indicators

    #f"The relative Strength Index (RSI) for {symbol} is {rsi}.   The MACD for {symbol} is {macd} and the MACD Signal is {macd_s}.  The Stochastics for {symbol} is %K: {prices['%K']} and %D: {prices['%D']}"
