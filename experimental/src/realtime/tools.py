import json
import random
import chainlit as cl
import openai
from datetime import datetime, timedelta
from realtime.functions.get_stock_quote import get_stock_quote_def, get_stock_quote
from realtime.functions.get_weather import get_weather_def, get_weather
from realtime.functions.get_stock_news import get_stock_news_def, get_stock_news
from realtime.functions.get_stock_technical_indicators import get_stock_technical_indicators_def, get_stock_technical_indicators
from realtime.functions.get_options_chain import get_options_chain_def, get_options_chain, OptionContract
from typing import List

# Tools list
tools = [
    (get_stock_quote_def, get_stock_quote),
    (get_weather_def, get_weather),
    (get_stock_news_def, get_stock_news),
    (get_stock_technical_indicators_def, get_stock_technical_indicators),
    (get_options_chain_def, get_options_chain)
]