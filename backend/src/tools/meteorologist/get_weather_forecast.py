import os
import requests
from pydantic import Field, BaseModel
from langchain.tools import tool

class WeatherInput(BaseModel):
    location: str = Field(description="The city, state and country, formatted like '<city>, <state>, <two letter country>'")

@tool("get_weather_forecast", args_schema=WeatherInput)
def get_weather_forecast (location: str) -> str:
    """
    Useful for getting the weather forecast for a given location
    """
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if api_key is None:
        raise ValueError("Please provide an API key for OpenWeather in the environment variable OPENWEATHER_API_KEY")
    
    url = f"https://api.openweathermap.org/data/2.5/forecast/daily?q={location}&cnt=10&appid={api_key}&units=imperial"
    
    response = requests.get(url)
    if response.status_code != 200:
        raise ValueError(f"Failed to get weather for {location}")
    else:
        return response.json()