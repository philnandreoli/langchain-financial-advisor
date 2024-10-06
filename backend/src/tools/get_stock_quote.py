import yfinance as yf
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from typing import Tuple

class StockQuoteInput(BaseModel):
    ticker: str = Field(description="The stock ticker symbol to return the quote for")

@tool("get_stock_quote", args_schema=StockQuoteInput)
def get_stock_quote(ticker: str) -> dict:
    """
    Used for getting the price and information about the stock for today.
    """
    prices = yf.Ticker(ticker)
    basic_info = dict(prices.fast_info)

    return {
        "basic_info": basic_info,
        "information": prices.info   
    }