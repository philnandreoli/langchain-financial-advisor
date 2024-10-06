import os
import requests
from typing import Dict, Union
from pydantic import Field,BaseModel
from langchain_core.tools import tool

POLYGON_BASE_URL = os.getenv("POLYGON_API_ENDPOINT")

class StockNewsInput(BaseModel):
    ticker: str = Field(description="The stock ticker symbol to return the news for")


@tool("get_stock_news", args_schema=StockNewsInput)
def get_stock_news(ticker: str) -> str:
    """
    Used for getting news for a given stock symbol
    """
    api_key = os.getenv("POLYGON_API_KEY")

    if not api_key:
        raise ValueError("No API key found for Polygon.io")
    
    url = f"{POLYGON_BASE_URL}v2/reference/news?ticker={ticker}&apiKey={api_key}"

    response = requests.get(url).json()
    status = response.get("status", None)

    if status != "OK":
        raise ValueError(f"Failed to get news for stock {ticker}.  API Error: {response}")
    
    return response.get("results", None)




