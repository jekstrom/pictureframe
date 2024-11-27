import requests
import urllib.parse
import json
import os
from datetime import datetime
from pathlib import Path
import boto3

class Weather:
    base_uri = "https://api.open-meteo.com/v1/forecast"

    def __init__(self, latitude, longitude, s3_cache_bucket):
        self.latitude = latitude
        self.longitude = longitude
        self.headers = {"accept": "application/json"}
        self.s3_cache_bucket = s3_cache_bucket
        
        self.weather_codes = []
        with open("mateo_wmo.json") as f:
            self.weather_codes = json.load(f)

        self.params = {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "current": ["temperature_2m", "is_day", "weather_code"],
            "hourly": ["temperature_2m", "weather_code"],
            "forecast_days": 2
        }

    def build_uri(self):
        return f"{self.base_uri}?latitude={self.params['latitude']}&longitude={self.params['longitude']}&current={','.join(self.params['current'])}&hourly={','.join(self.params['hourly'])}&forecast_days={self.params['forecast_days']}"

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

    def get_weather(self, metric, location, day, hour):
        # Get cached response if it exists
        filename = (
            f"weather_data__{location.replace(' ', '')}_{day}_{hour}.json"
        )
        weather_data = self.get_data(filename, self.build_uri())

        current_weather = self.weather_codes["weatherCode"][
            f"{weather_data['current']['weather_code']}"
        ]
        temperature = weather_data["current"]["temperature_2m"]
        is_night = weather_data["current"]["is_day"] == 0

        hourly = weather_data["hourly"]
        forecast_weather = hourly["temperature_2m"][-4]
        forecast_temperature = hourly["weather_code"][-4]

        if metric:
            temperature = round(temperature, 1)
        else:
            temperature = round((temperature * (9 / 5)) + 32, 1)

        return (current_weather, temperature, "nighttime" if is_night else "daytime", forecast_weather, forecast_temperature)
