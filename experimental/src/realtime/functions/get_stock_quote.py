import yfinance as yf

get_stock_quote_def = {
    "name": "get_stock_quote",
    "description": "Used for getting the price and information about the stock for today.",
    "parameters": {
      "type": "object",
      "properties": {
        "ticker": {
          "type": "string",
          "description": "The stock ticker symbol to return the quote for"
        }
      },
      "required": ["ticker"]
    }
}

async def get_stock_quote(ticker: str) -> dict:
    prices = yf.Ticker(ticker)

    return {
        "information": prices.info   
    }