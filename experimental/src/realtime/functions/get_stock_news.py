import os
import requests
from typing import Dict, Union

POLYGON_BASE_URL = os.getenv("POLYGON_API_ENDPOINT")

get_stock_news_def = {
    "name": "get_stock_news",
    "description": "Used for getting news for a given stock symbol",
    "parameters": {
      "type": "object",
      "properties": {
        "ticker": {
          "type": "string",
          "description": "The stock ticker symbol to return the news for"
        },
      },
      "required": ["ticker"]
    }
}

async def get_stock_news(ticker: str) -> str:
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




