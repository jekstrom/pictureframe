import sys
from datetime import datetime
from image_creator import ImageCreator
from weather import Weather
from weather_bot import WeatherBot
import pytz

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
    is_metric,
    None,
    0,
)

weather_bot = WeatherBot(
    temperature,
    current_weather,
    location,
    todays_date,
    sun_string,
    is_metric,
    "",
)

prompt = weather_bot.get_prompt()
weather_bot.gen_image(prompt, image_creator)
