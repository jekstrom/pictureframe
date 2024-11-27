#!/usr/bin/sh

set -e

pip install --target ./lambda-packages -r requirements.txt --no-user
cd lambda-packages/
zip -r ../lambda-packages.zip .
cd ..
zip -j lambda-packages.zip infra/lambda/handler.py
cd infra/lambda/
zip -r ../../lambda-packages.zip fonts/
cd ../..
zip -j lambda-packages.zip genimage.py
zip -j lambda-packages.zip image_creator.py
zip -j lambda-packages.zip weather_bot.py
zip -j lambda-packages.zip weather.py
zip -j lambda-packages.zip weathercodes.json
zip -j lambda-packages.zip mateo_wmo.json
