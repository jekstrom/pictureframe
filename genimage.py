from datetime import datetime
from image_creator import ImageCreator
from weather import Weather
from weather_bot import WeatherBot

location = "Bellevue WA"
is_metric = False
todays_date = datetime.today().strftime("%Y-%m-%d")
current_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

weather_api = Weather(location)
sun_string = weather_api.get_sunstring()
current_weather, temperature = weather_api.get_weather(is_metric)

degree_text = "°C" if is_metric else "°F"
print(
    f"Current weather for {location}: {temperature}{degree_text} {current_weather}. It is {sun_string}."
)

image_creator = ImageCreator(
    temperature, location, current_weather, todays_date, is_metric
)

weather_bot = WeatherBot(
    temperature, current_weather, location, todays_date, sun_string, is_metric
)
prompt = weather_bot.get_prompt()
weather_bot.gen_image(prompt, image_creator, "weather_image.jpg")
