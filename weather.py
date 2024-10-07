import requests
import urllib.parse
import json
import os
from datetime import datetime
from pathlib import Path
import boto3


class Weather:
    base_uri = "https://api.tomorrow.io/v4/weather/"

    def __init__(self, location, s3_cache_bucket):
        self.location = location
        self.api_key = os.getenv("TOMORROW_API_KEY")
        self.headers = {"accept": "application/json"}
        self.s3_cache_bucket = s3_cache_bucket

        self.weather_codes = []
        with open("weathercodes.json") as f:
            self.weather_codes = json.load(f)

        self.realtime_url = f"{self.base_uri}realtime?location={urllib.parse.quote_plus(location)}&apikey={self.api_key}"
        self.forecast_url = f"{self.base_uri}forecast?location={urllib.parse.quote_plus(location)}&timesteps=1d&units=metric&apikey={self.api_key}"

    def get_data(self, filename, url):
        data = {}
        if self.s3_cache_bucket:
            s3 = boto3.resource("s3")

            exists = False
            try:
                s3.Object(self.s3_cache_bucket, filename).load()
                exists = True
            except Exception as ex:
                print(ex)
                pass

            if exists:
                print("Using cached weather data")
                obj = s3.Object(self.s3_cache_bucket, filename)
                data = json.loads(obj.get()["Body"].read().decode("utf-8"))
            else:
                print("Making Weather API Call")
                forecast_response = requests.get(url, headers=self.headers)
                data = json.loads(forecast_response.text)
                obj = s3.Object(self.s3_cache_bucket, filename)
                obj.put(Body=(bytes(json.dumps(data).encode("utf-8"))))
        else:
            data_path = Path(filename)
            if not data_path.exists():
                forecast_response = requests.get(url, headers=self.headers)
                data = json.loads(forecast_response.text)
                with open(filename, "w") as f:
                    json.dump(data, f)
            else:
                with open(filename) as f:
                    data = json.load(f)
        return data

    def get_sunstring(self, day):
        # Get cached response if it exists
        forecast_filename = f"forecast_data_{day}.json"
        forecast_weather_data = self.get_data(forecast_filename, self.forecast_url)

        dateformat = "%Y-%m-%dT%H:%M:%SZ"
        data = forecast_weather_data["timelines"]["daily"][0]["values"]
        sunrise_time = datetime.strptime(data["sunriseTime"], dateformat)
        sunset_time = datetime.strptime(data["sunsetTime"], dateformat)

        is_night = datetime.utcnow() > sunset_time
        return "nighttime" if is_night else "daytime"

    def get_weather(self, metric, day):
        # Get cached response if it exists
        realtime_filename = f"realtime_data_{day}.json"
        realtime_weather_data = self.get_data(realtime_filename, self.realtime_url)

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
