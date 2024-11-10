import sys
from datetime import datetime
from image_creator import ImageCreator
from weather import Weather
from weather_bot import WeatherBot
import pytz
import random

location = sys.argv[1]
timezone = sys.argv[2]
is_metric = sys.argv[3] == "True"
now = datetime.utcnow()
todays_date = datetime.today().strftime("%Y-%m-%d")
current_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

py_timezone = pytz.timezone(timezone)
local_time = datetime.now(py_timezone)
display_date = local_time.strftime("%Y-%m-%d")

day_of_week = now.strftime("%A")
todays_date = now.strftime("%Y-%m-%d")
current_time = now.strftime("%Y-%m-%d %H:%M:%S")
current_hour = now.strftime("%H")

weather_api = Weather(location, None)
sun_string = weather_api.get_sunstring(location, todays_date, current_hour)
current_weather, temperature = weather_api.get_weather(
    is_metric, location, todays_date, current_hour
)
forecast_weather, forecast_temperature = weather_api.get_forecast_weather(
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
    forecast_weather,
    forecast_temperature,
    todays_date,
    display_date,
    sun_string,
    is_metric,
    None,
    0,
)

random_details = [
    ", include a famous landmark or parks",
    ", include a statue",
    ", include walking people",
    ", focusing on the landscape",
    ", low angle",
    ", specifically a gritty scene",
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
    "art nouveau",
    "abstract" "surrealist",
    "baroque",
    "neoclassicist",
    "classic",
    "art deco",
    "bauhaus",
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
