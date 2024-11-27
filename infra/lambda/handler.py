import boto3
import botocore
import sys
import os
from datetime import datetime, timedelta
import pytz
import croniter
from image_creator import ImageCreator
from weather import Weather
from weather_bot import WeatherBot
import random


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
    latitude = event["latitude"]
    longitude = event["longitude"]
    timezone = event["timezone"]
    is_metric = event["is_metric"] == "True"
    now = datetime.utcnow()
    py_timezone = pytz.timezone(timezone)
    local_time = datetime.now(py_timezone)

    display_date = local_time.strftime("%Y-%m-%d")

    day_of_week = now.strftime("%A")
    todays_date = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%Y-%m-%d %H:%M:%S")
    current_hour = now.strftime("%H")

    weather_api = Weather(latitude, longitude, os.getenv("S3_CACHE_BUCKET"))
    current_weather, temperature, sun_string, forecast_weather, forecast_temperature = weather_api.get_weather(
        is_metric, location, todays_date, current_hour
    )

    degree_text = "°C" if is_metric else "°F"
    print(
        f"Current weather for {location}: {temperature}{degree_text} {current_weather}. It is {sun_string}."
    )

    # Get next run time in microseconds
    cron_expr = os.getenv("CRON_EXPRESSION")
    cron = croniter.croniter(cron_expr, now + timedelta(minutes=1))
    next_date = cron.get_next(datetime)
    print(f"next run time: {next_date.strftime('%Y-%m-%d %H:%M:%S')}")
    next_run_time = int(next_date.timestamp())

    image_creator = ImageCreator(
        temperature,
        location,
        current_weather,
        forecast_weather,
        forecast_temperature,
        todays_date,
        display_date,
        sun_string,
        is_metric,
        os.getenv("S3_IMAGE_BUCKET"),
        next_run_time,
    )

    random_details = [
        ", include a famous landmark or parks",
        ", include a statue",
        ", include walking people",
        ", focusing on the landscape",
        ", low angle",
        ", specifically a gritty scene",
        ", interior looking out a close window",
        ", from ground level in a park",
        "",
    ]
    details = random_details[random.randint(0, len(random_details) - 1)]
    print(f"Details: {details}")

    random_style = [
        "minimalist",
        "impressionist",
        "expressionist",
        "realistic",
        "cubist",
        "futurist",
        "retro",
        "retro futurist",
        "art nouveau",
        "abstract",
        "surrealist",
        "baroque",
        "neoclassicist",
        "classic",
        "art deco",
        "bauhaus",
        "pixel",
    ]
    style = random_style[random.randint(0, len(random_style) - 1)]
    print(f"Style: {style}")

    weather_bot = WeatherBot(
        temperature,
        current_weather,
        location,
        todays_date,
        sun_string,
        is_metric,
        details,
        style,
    )
    prompt = weather_bot.get_prompt()
    weather_bot.gen_image(prompt, image_creator)
