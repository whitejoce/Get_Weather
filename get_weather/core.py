import re
from pathlib import Path
from typing import Iterable

from .client import WeatherClient, create_headers
from .cli import run_weather_process
from .exceptions import InvalidCityNameError
from .parser import parse_alarm_lines

_default_client = WeatherClient()


def dumpResponse(response: str, path: str | Path = "response.html") -> None:
    Path(path).write_text(response, encoding="utf-8")


def get_CityName() -> tuple[str, str]:
    return _default_client.get_city_name()


def get_city_code(city: str) -> str:
    return _default_client.get_city_code(city)


def get_weaPage(url: str, headers: dict[str, str] | None = None) -> str:
    return _default_client.get_page(url, headers=headers)


def CheckInput(InputString: str) -> bool:
    if not InputString or InputString.isspace():
        return True
    if any(char.isdigit() for char in InputString):
        return True
    return re.search(r"[a-zA-Z]+$", InputString) is not None


def get_weather(City_code: str, dump_response_path: str | Path | None = None) -> str:
    return _default_client.get_weather(City_code, dump_response_path=dump_response_path)


def weather_alarm(alarm_list: str) -> Iterable[str]:
    return parse_alarm_lines(alarm_list)


def main_weather_process(
    output: int = 0,
    city_name: str | None = None,
    dump_response_path: str | Path | None = None,
) -> str:
    if city_name and CheckInput(city_name):
        raise InvalidCityNameError("检测到非地名字符")
    return run_weather_process(
        output=output,
        city_name=city_name,
        dump_response_path=dump_response_path,
        client=_default_client,
    )


def debug_mode(
    city: str,
    output_file: str | Path | None = "debug_results.json",
) -> list[dict[str, object]]:
    return _default_client.debug_urls(city, output_file=output_file)
