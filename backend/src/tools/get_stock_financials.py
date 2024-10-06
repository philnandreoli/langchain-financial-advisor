import os
import requests
from typing import Dict, Union
from pydantic import Field, BaseModel
from typing import Optional
from langchain_core.tools import tool

POLYGON_BASE_URL = os.getenv("POLYGON_API_ENDPOINT")

class StockFinancialsInput(BaseModel):
    ticker: str = Field(description="The stock ticker symbol to return the news for")
    filing_date: Optional[str] = Field(description="The date of the filing in the format YYYY-MM-DD")

@tool("get_stock_financials", args_schema=StockFinancialsInput)
def get_stock_financials(ticker: str, filing_date: Optional[str]) -> str:
    """
    Used for getting the stock financials from their 10-K and 10-Q reports
    """
    api_key = os.getenv("POLYGON_API_KEY")

    if not api_key:
        raise ValueError("No API key found for Polygon.io")
    
    url = f"{POLYGON_BASE_URL}vX/reference/financials?ticker={ticker}&apiKey={api_key}"

    if filing_date:
        url += f"&filing_date={filing_date}"

    response = requests.get(url).json()
    status = response.get("status", None)

    if status != "OK":
        raise ValueError(f"Failed to get news for stock {ticker}.  API Error: {response}")
    
    return response.get("results", None)