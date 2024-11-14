import numpy as np 
import pandas as pd
import pandas_ta as ta
import yfinance as yf
from pydantic import Field, BaseModel
from langchain_core.tools import tool
from typing import List
from datetime import datetime, timedelta
import pytz

K_PERIOD=14
D_PERIOD=3

get_stock_technical_indicators_def = {
    "name": "get_stock_technical_indicators",
    "description": "Used for getting the technical indicators and historical data for a stock symbol.",
    "parameters": {
      "type": "object",
      "properties": {
        "ticker": {
          "type": "string",
          "description": "The stock symbol to get technical indicators and historical data for"
        }
      },
      "required": ["ticker"]
    }
}



class StockTechnicalIndicatorInput(BaseModel):
    ticker: str = Field(description="The stock symbol to get technical indicators and historical data for")

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
    ma_50: float = Field(description="The 50-day moving average of the stock")
    ma_200: float = Field(description="The 200-day moving average of the stock")
    death_cross_signal: float = Field(description="The death cross signal value")
    death_cross: float = Field(description="The death cross value")
    golden_cross_signal: float = Field(description="The golden cross signal value")
    golden_cross: float = Field(description="The golden cross value")
    obv: float = Field(description="The On-Balance Volume value")

# Helper Functions
def calculate_macd(prices):
    prices.ta.macd(close="Close", fast=12, slow=26, signal=9, append=True)
    prices.rename(columns={"MACD_12_26_9": "macd", "MACDs_12_26_9": "macd_signal", "MACDh_12_26_9": "macd_histogram"}, inplace=True)

def calculate_stochastics(prices):
    prices["n_high"] = prices["High"].rolling(K_PERIOD).max()
    prices["n_low"] = prices["Low"].rolling(K_PERIOD).min()
    prices["K"] = (prices["Close"] - prices["n_low"]) * 100 / (prices["n_high"] - prices["n_low"])
    prices["D"] = prices['K'].rolling(D_PERIOD).mean()

def calculate_moving_averages(prices):
    prices["ma_50"] = prices["Close"].rolling(window=50).mean()
    prices["ma_200"] = prices["Close"].rolling(window=200).mean()

def calculate_cross_signals(prices):
    prices["death_cross_signal"] = prices['ma_50'] < prices['ma_200']
    prices["death_cross"] = prices["death_cross_signal"].diff()
    prices["golden_cross_signal"] = prices['ma_50'] > prices['ma_200']
    prices['golden_cross'] = prices['golden_cross_signal'].diff()

#Calculate Relative Strength Index
def calculate_rsi(prices):
    delta = prices["Close"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(7).mean()
    avg_loss = loss.rolling(7).mean()
    rs = avg_gain / avg_loss
    prices["rsi"] = 100 - (100 / (1 + rs))

#Calculate Average Daily Range
def calculate_adr(prices):
    prices["dr"] = prices["High"] - prices["Low"]
    prices["adr"] = prices["dr"].rolling(7).mean()

#Calculate On-Balance Volume
def calculate_obv(prices):
    prices["obv"] = (np.sign(prices["Close"].diff()) * prices["Volume"]).fillna(0).cumsum()

def format_prices(prices):
    prices.index = prices.index.strftime("%Y-%m-%d")
    prices.drop(columns=["Dividends", "Stock Splits"], axis=1, inplace=True)
    prices.rename(columns={"Date": "date", "Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"}, inplace=True)
    prices.rename_axis("date", inplace=True)

async def get_stock_technical_indicators(ticker: str) -> List[StockTechnicalIndicatorOutput]:
    """
    Used for getting the technical indicators and historical data for a stock symbol.
    """
    try:
        prices = yf.Ticker(ticker).history(period="1y")
        calculate_macd(prices)
        calculate_stochastics(prices)
        calculate_moving_averages(prices)
        calculate_cross_signals(prices)
        calculate_rsi(prices)
        calculate_adr(prices)
        calculate_obv(prices)

        # Filter for the last 6 months
        tz = 'America/New_York'
        six_months_ago = datetime.now(pytz.timezone(tz)) - timedelta(days=6*30)
        prices = prices[prices.index >= six_months_ago] 
        format_prices(prices)

        stock_technical_indicators = prices.reset_index().to_dict(orient='records')
        #technical_indicators: List[StockTechnicalIndicatorOutput] = [StockTechnicalIndicatorOutput(**item) for item in stock_technical_indicators]

        return stock_technical_indicators
    except Exception as e:
        print(f"Error fetching stock data: {e}")
        return []