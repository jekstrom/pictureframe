import io
import requests
from openai import OpenAI
from image_creator import ImageCreator
from PIL import Image


class WeatherBot:
    def __init__(
        self, temperature, current_weather, location, todays_date, sun_string, metric
    ):
        self.client = OpenAI()
        self.temperature = temperature
        self.current_weather = current_weather
        self.location = location
        self.todays_date = todays_date
        self.sun_string = sun_string
        self.metric = metric

    def get_prompt(self):
        prompt = f"Create a prompt I can use to generate an image of the {self.temperature}{'C' if self.metric else 'F'} {self.current_weather} weather for {self.location} for {self.todays_date}. I want a masterful and traditional artistic painting. Reply with only the prompt. It should be distinctly {self.sun_string} {self.location}. Be as verbose as possible. Do not include any text or icons."
        completion = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert genai prompt engineer. You help generate prompts for AI image generation for a simple e-ink display of the current weather.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        )

        return completion.choices[0].message.content

    def gen_image(self, prompt, image_creator):
        print(prompt)

        response = self.client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
            style="vivid",
        )

        image_url = response.data[0].url
        print(image_url)

        img_data = requests.get(image_url).content
        print(f"img_data length: {len(img_data)}")

        image_creator.getbuffer(Image.open(io.BytesIO(img_data)))
