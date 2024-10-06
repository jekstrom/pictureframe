import requests
import urllib.parse
import json
import os
from datetime import datetime
from pathlib import Path


class Weather:
    base_uri = "https://api.tomorrow.io/v4/weather/"

    def __init__(self, location):
        self.location = location
        self.api_key = os.getenv("TOMORROW_API_KEY")
        self.headers = {"accept": "application/json"}

        self.weather_codes = []
        with open("weathercodes.json") as f:
            self.weather_codes = json.load(f)

        self.realtime_url = f"{self.base_uri}realtime?location={urllib.parse.quote_plus(location)}&apikey={self.api_key}"
        self.forecast_url = f"{self.base_uri}forecast?location={urllib.parse.quote_plus(location)}&timesteps=1d&units=metric&apikey={self.api_key}"

    def get_sunstring(self):
        # Get cached response if it exists
        forecast_filename = "forecast_data.json"
        data_path = Path(forecast_filename)
        forecast_weather_data = {}
        if not data_path.exists():
            print("Making API Request")
            forecast_response = requests.get(self.forecast_url, headers=self.headers)
            forecast_weather_data = json.loads(forecast_response.text)
            with open(forecast_filename, "w") as f:
                json.dump(forecast_weather_data, f)
        else:
            with open(forecast_filename) as f:
                forecast_weather_data = json.load(f)

        dateformat = "%Y-%m-%dT%H:%M:%SZ"
        data = forecast_weather_data["timelines"]["daily"][0]["values"]
        sunrise_time = datetime.strptime(data["sunriseTime"], dateformat)
        sunset_time = datetime.strptime(data["sunsetTime"], dateformat)

        is_night = datetime.utcnow() > sunset_time
        return "nighttime" if is_night else "daytime"

    def get_weather(self, metric):
        # Get cached response if it exists
        realtime_filename = "realtime_data.json"
        data_path = Path(realtime_filename)
        realtime_weather_data = {}
        if not data_path.exists():
            print("Making API Request")
            realtime_response = requests.get(self.realtime_url, headers=self.headers)
            realtime_weather_data = json.loads(realtime_response.text)
            with open(realtime_filename, "w") as f:
                json.dump(realtime_weather_data, f)
        else:
            with open(realtime_filename) as f:
                realtime_weather_data = json.load(f)

        realtime_data = realtime_weather_data["data"]["values"]
        current_weather = self.weather_codes["weatherCode"][
            f"{realtime_data['weatherCode']}"
        ]
        temperature = realtime_data["temperature"]

        if metric:
            temperature = round(temperature, 1)
        else:
            temperature = round((temperature * (9 / 5)) + 32, 1)

        return (current_weather, temperature)
