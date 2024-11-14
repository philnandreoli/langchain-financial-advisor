import yfinance as yf
from langchain_core.tools import tool
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
import json


get_options_chain_def = {
    "name": "get_options_chain",
    "description": "Used for getting the options chain/contracts for a specific stock",
    "parameters": {
      "type": "object",
      "properties": {
        "ticker": {
          "type": "string",
          "description": "The stock ticker symbol to return the quote for"
        },
        "strike_price": {
            "type": "number",
            "description": "The strike price of the Option"
        },
        "contract_type": {
            "type": "string",
            "description": "The type of option contract to get.  The options are 'call' or 'put'"
        }
      },
      "required": ["ticker"],
      "additionalProperties": False 
    }
}



class OptionsChainInput(BaseModel):
    ticker: str = Field(description="The stock ticker symbol to return the quote for")
    strike_price: Optional[float] = Field("The strike price of the Option")
    contract_type: Optional[str] = Field("The type of option contract to get.  The options are 'call' or 'put'")

class OptionContract(BaseModel):
    contractSymbol: str = Field("The symbol for the option contract in the format: SYMBOLYYMMDDCXXXXX or SYMBOLYYMMDDPXXXXX where C is a Call and P is a put and XXXXX is the strike price ")
    strike: float = Field("The strike price of the option contract")
    lastPrice: float = Field("The last trade price of the option contract")
    bid: float = Field("The bid price of the option contract")
    ask: float = Field("The ask price of the option contract")
    change: float = Field("The change in price of the option contract")
    percentChange: float = Field("The percent change in price of the option contract")
    volume: float = Field("The volume of the option contract")
    openInterest: int = Field("The open interest of the option contract") 
    impliedVolatility: float = Field("The implied volatility of the option contract")
    inTheMoney: bool = Field("Whether the option contract is in the money")
    expiration: str = Field("The expiration date of the option contract")
    lastTradeDate: datetime = Field("The last trade date of the option contract")

    def to_dict(self):
        return self.model_dump_json()

async def get_options_chain(
    ticker: str,
    strike_price: Optional[float] = None,
    contract_type: Optional[str] = None
) -> List[OptionContract]:
    """
    Used for getting the options chain/contracts for a specific stock
    """
    ticker = yf.Ticker(ticker)
    options = ticker.options[:4]
    option_contracts: []

    for option in options:
        option_chain = ticker.option_chain(option)
        calls = option_chain.calls
        puts = option_chain.puts

        def filter_options(df, contract_type):
            if strike_price is not None:
                df = df[df['strike'] >=  strike_price]
            return [OptionContract(**row) for _, row in df[df['inTheMoney'] == False].iterrows()]

        try:
            if contract_type is None:
                option_contracts.append(filter_options(calls, 'call'))
                option_contracts.append(filter_options(puts, 'put'))
            elif contract_type == 'call':
                option_contracts.append(filter_options(calls, 'call'))
            elif contract_type == 'put':
                option_contracts.append(filter_options(puts, 'put'))
            else:
                raise ValueError(f"Invalid contract_type: {contract_type}")
        except Exception as e:
            print(f"Error: {e}")


    return option_contracts.to