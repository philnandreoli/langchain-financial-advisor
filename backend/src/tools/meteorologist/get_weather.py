import os
import requests
from pydantic import Field, BaseModel
from langchain.tools import tool

class WeatherInput(BaseModel):
    location: str = Field(description="The city, state and country, formatted like '<city>, <state>, <two letter country>'")

@tool("get_weather", args_schema=WeatherInput)
def get_weather (location: str) -> str:
    """
    Useful for getting the current weather for a given location
    """
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if api_key is None:
        raise ValueError("Please provide an API key for OpenWeather in the environment variable OPENWEATHER_API_KEY")
    
    url = f"https://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units=imperial"
    response = requests.get(url)
    if response.status_code != 200:
        raise ValueError(f"Failed to get weather for {location}")
    else:
        #weather_condition = response.json()["weather"][0]["description"]
        #temperature = response.json()["main"]["temp"]

        return response.json()