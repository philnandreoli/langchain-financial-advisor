import os
import requests

get_weather_def = {
    "name": "get_weather",
    "description": "Useful for getting the weather for a given location",
    "parameters": {
      "type": "object",
      "properties": {
        "location": {
          "type": "string",
          "description": "The city, state and country, formatted like '<city>, <state>, <two letter country>'"
        }
      },
      "required": ["location"]
    }
}

async def get_weather (location: str) -> str:
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