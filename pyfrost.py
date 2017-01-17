#!/usr/bin/python2.7
"""
App to send weather report to a phone number using twilio and OpenWeather.
"""

# Lines 7-10 to enable free hosting on pythonanywhere.com
import os
from urlparse import urlparse
from twilio.rest.resources import Connection
from twilio.rest.resources.connection import PROXY_TYPE_HTTP

from twilio.rest import TwilioRestClient
from pyowm import OWM
from datetime import datetime, timedelta
import pytz

# Proxy details for twilio to enable free hosting on pythonanywhere.com
host, port = urlparse(os.environ["http_proxy"]).netloc.split(":")
Connection.set_proxy_info(
    host,
    int(port),
    proxy_type=PROXY_TYPE_HTTP,
)

# Authentication details
ACCOUNT_SID = 'account_sid'
AUTH_TOKEN = 'auth_token'
OWM_API_KEY = 'owm_api_key'

# Phone numbers
FROM_NUMBER = 'twilio_number'
TO_NUMBER = 'your_number'

# Weather report variables
location = 'location_name'
eleven_hours_from_now = pytz.utc.localize(datetime.now() + timedelta(hours=11))
cloud_threshold = 75
rain_threshold = 2.0
temp_threshold = 1.0

# Initialise twilio client
client = TwilioRestClient(ACCOUNT_SID, AUTH_TOKEN)

# Initialise OpenWeatherMap
owm = OWM(OWM_API_KEY)

# Get weather report
fc = owm.three_hours_forecast(location)
f = fc.get_forecast()
weather_objects = f.get_weathers()

forecasts = [{'time': weather.get_reference_time('date').time()
                                                        .strftime('%H:%M'),
              'min_temp': weather.get_temperature('celsius')['temp_min'],
              'cloud_cover': weather.get_clouds(),
              'rain': weather.get_rain()['3h'] if weather.get_rain() else 0.0}
             for weather
             in weather_objects
             if weather.get_reference_time('date') < eleven_hours_from_now]

avg_cloud = sum(forecast['cloud_cover']
                for forecast in forecasts) / len(forecasts)
total_rain = sum(forecast['rain'] for forecast in forecasts)
avg_temp = sum(forecast['min_temp'] for forecast in forecasts) / len(forecasts)

# Crude way of deciding if message worth sending...
if (avg_cloud < cloud_threshold and
    total_rain < rain_threshold and
        avg_temp < temp_threshold):
    # Unicode emojis included
    report_title = u'\u2744 There might be frost tomorrow morning! \u2744\n'
    report_body = u'\U0001F321 {} \u00b0C \n\u2614 {} mm\n\u2601 {}%'.format(
        avg_temp,
        total_rain,
        avg_cloud)
    message_body = report_title + report_body
    message = client.messages.create(body=message_body,
                                     to=TO_NUMBER,
                                     from_=FROM_NUMBER)
