#!/usr/bin/python
# _*_coding: utf-8 _*_
# Coder:Whitejoce

import sys

from get_weather import (
    CheckInput,
    WeatherClient,
    create_headers,
    debug_mode,
    get_CityName,
    get_city_code,
    get_weaPage,
    get_weather,
    main_weather_process,
    weather_alarm,
)
from get_weather.cli import main
from get_weather.core import dumpResponse

__all__ = [
    "CheckInput",
    "WeatherClient",
    "create_headers",
    "debug_mode",
    "dumpResponse",
    "get_CityName",
    "get_city_code",
    "get_weaPage",
    "get_weather",
    "main_weather_process",
    "weather_alarm",
]


if __name__ == "__main__":
    sys.exit(main())
