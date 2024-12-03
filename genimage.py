import sys
from datetime import datetime
from image_creator import ImageCreator
from weather import Weather
from weather_bot import WeatherBot
import pytz
import random

location = sys.argv[1]
latitude = sys.argv[2]
longitude = sys.argv[3]
timezone = sys.argv[4]
is_metric = sys.argv[5] == "True"
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

weather_api = Weather(latitude, longitude, None)
current_weather, temperature, sun_string, forecast_weather, forecast_temperature = (
    weather_api.get_weather(is_metric, location, todays_date, current_hour)
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
    ", include a portrait of a person outside",
    ", focusing on the landscape",
    ", low angle looking up",
    ", specifically a gritty scene",
    ", interior looking out a close window",
    ", with a cozy log cabin",
    ", from a campsite",
    ", from ground level in a park",
    ", calm and serene",
    ", chaotic and crazy",
    ", with a hidden message",
    ", with animals",
    ", with coffee",
    ", with a campfire",
    ", from a canoe",
    ", include outdoor activities",
    "",
]
if "Heavy" in current_weather or "Thunderstorm" in current_weather:
    details = ", emphasize the extreme weather situation"
else:
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
    "geometric",
    "avant garde",
    "brutalist",
    "digital",
    "fine art",
    "renaissance",
    "hyperrealism",
    "Japonisme",
    "psychedelic",
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
