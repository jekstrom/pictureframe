import boto3
import botocore
import sys
import os
from datetime import datetime
from image_creator import ImageCreator
from weather import Weather
from weather_bot import WeatherBot


def lambda_handler(event, context):
    print(f"boto3 version: {boto3.__version__}")
    print(f"botocore version: {botocore.__version__}")

    client = boto3.client("ssm")
    tomorrow_api_key = client.get_parameter(
        Name=os.getenv("TOMORROW_API_PARAMETER"), WithDecryption=True
    )
    openai_api_key = client.get_parameter(
        Name=os.getenv("OPENAI_API_PARAMETER"), WithDecryption=True
    )
    os.environ["TOMORROW_API_KEY"] = tomorrow_api_key["Parameter"]["Value"]
    os.environ["OPENAI_API_KEY"] = openai_api_key["Parameter"]["Value"]

    location = event["location"]
    is_metric = event["is_metric"] == "True"
    now = datetime.utcnow()
    todays_date = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%Y-%m-%d %H:%M:%S")
    current_hour = now.strftime("%H")

    weather_api = Weather(location, os.getenv("S3_CACHE_BUCKET"))
    sun_string = weather_api.get_sunstring(location, todays_date, current_hour)
    current_weather, temperature = weather_api.get_weather(
        is_metric, location, todays_date, current_hour
    )

    degree_text = "°C" if is_metric else "°F"
    print(
        f"Current weather for {location}: {temperature}{degree_text} {current_weather}. It is {sun_string}."
    )

    image_creator = ImageCreator(
        temperature,
        location,
        current_weather,
        todays_date,
        is_metric,
        os.getenv("S3_IMAGE_BUCKET"),
    )

    weather_bot = WeatherBot(
        temperature, current_weather, location, todays_date, sun_string, is_metric
    )
    prompt = weather_bot.get_prompt()
    weather_bot.gen_image(prompt, image_creator)
