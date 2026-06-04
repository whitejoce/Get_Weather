import json
from pathlib import Path

import pytest
import requests

from get_weather.client import WeatherClient, create_headers
from get_weather.exceptions import CityNotFoundError, NetworkError


class FakeResponse:
    def __init__(self, content: str, status_code: int = 200) -> None:
        self.content = content.encode("utf-8")
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} error")


class FakeSession:
    def __init__(self, responses: dict[str, str | FakeResponse | Exception]) -> None:
        self.responses = responses
        self.calls: list[dict[str, object]] = []

    def get(self, url: str, headers=None, timeout=None):
        self.calls.append({"url": url, "headers": headers, "timeout": timeout})
        for key, response in self.responses.items():
            if key in url:
                if isinstance(response, Exception):
                    raise response
                if isinstance(response, FakeResponse):
                    return response
                return FakeResponse(response)
        raise requests.ConnectionError(f"unexpected url: {url}")


SAMPLE_CITY = {
    "name": "测试城市",
    "area_id": "999000111",
    "name_en": "sample-city",
}
SAMPLE_DATA_SK = {
    "nameen": SAMPLE_CITY["name_en"],
    "cityname": SAMPLE_CITY["name"],
    "weather": "测试天气",
    "temp": "24",
    "SD": "55%",
    "time": "09:30",
    "aqi": "42",
    "aqi_pm25": "21",
    "date": "01月02日(星期三)",
}
SAMPLE_TEMP = {"temp": "28℃", "tempn": "18℃"}
SAMPLE_DATA_ZS = {"ys_des_s": "测试雨具建议。"}
SAMPLE_QWEATHER = {
    "summary": "测试天气摘要。",
    "aqi_level": "良",
}


def make_city_js(city: dict[str, str] = SAMPLE_CITY) -> str:
    payload = {
        "province": {
            "city": {
                "NAMECN": city["name"],
                "AREAID": city["area_id"],
            }
        }
    }
    return f"var city_data={json.dumps(payload, ensure_ascii=False)};"


def make_weather_index(
    data_sk: dict[str, str] = SAMPLE_DATA_SK,
    data_zs: dict[str, str] = SAMPLE_DATA_ZS,
) -> str:
    return "\n".join(
        [
            'var alarmDZ = {"w":[]};',
            f"var dataSK = {json.dumps(data_sk, ensure_ascii=False)};",
            f'var dataZS = {json.dumps({"zs": data_zs, "cn": data_sk["cityname"]}, ensure_ascii=False)};',
        ]
    )


def make_temp_html(temp: dict[str, str] = SAMPLE_TEMP) -> str:
    return f'var cityDZ={{"weatherinfo":{json.dumps(temp, ensure_ascii=False)}}};'


def make_qweather_html(qweather: dict[str, str] = SAMPLE_QWEATHER) -> str:
    return (
        f'<div class="current-abstract">{qweather["summary"]}</div>'
        f'<p class="city-air-chart__txt text-center">{qweather["aqi_level"]}</p>'
    )


def test_create_headers_adds_optional_cookie_and_referer() -> None:
    headers = create_headers(cookie="a=b", referer="https://example.com")

    assert "User-Agent" in headers
    assert headers["Cookie"] == "a=b"
    assert headers["Referer"] == "https://example.com"


def test_get_city_code_finds_nested_city() -> None:
    client = WeatherClient(session=FakeSession({"city.js": make_city_js()}))

    assert client.get_city_code(SAMPLE_CITY["name"]) == SAMPLE_CITY["area_id"]


def test_get_city_code_raises_when_city_missing() -> None:
    client = WeatherClient(session=FakeSession({"city.js": make_city_js()}))

    with pytest.raises(CityNotFoundError):
        client.get_city_code("不存在")


def test_get_weather_formats_text_without_default_dump(tmp_path: Path) -> None:
    client = WeatherClient(
        session=FakeSession(
            {
                "weather_index": make_weather_index(),
                "dingzhi": make_temp_html(),
                "qweather.com": make_qweather_html(),
            }
        )
    )

    text = client.get_weather(SAMPLE_CITY["area_id"])

    assert f"定位城市:  {SAMPLE_DATA_SK['cityname']}" in text
    assert f"实时天气:  {SAMPLE_DATA_SK['weather']}" in text
    assert f"体感温度:  {SAMPLE_DATA_SK['temp']}℃" in text
    assert f"温度区间:  {SAMPLE_TEMP['temp']} ~ {SAMPLE_TEMP['tempn']}" in text
    assert f"空气质量:  {SAMPLE_DATA_SK['aqi']}({SAMPLE_QWEATHER['aqi_level']})" in text
    assert f"雨具携带:  {SAMPLE_DATA_ZS['ys_des_s']}" in text
    assert SAMPLE_QWEATHER["summary"] in text
    assert not (tmp_path / "response.html").exists()


def test_get_weather_writes_dump_only_when_requested(tmp_path: Path) -> None:
    client = WeatherClient(
        session=FakeSession(
            {
                "weather_index": make_weather_index(),
                "dingzhi": make_temp_html(),
                "qweather.com": make_qweather_html(),
            }
        )
    )
    dump_path = tmp_path / "response.html"

    client.get_weather(SAMPLE_CITY["area_id"], dump_response_path=dump_path)

    assert dump_path.read_text(encoding="utf-8") == make_weather_index()


def test_get_page_keeps_legacy_prettified_html() -> None:
    client = WeatherClient(session=FakeSession({"example.com": "<html><body>x</body></html>"}))

    text = client.get_page("https://example.com")

    assert "<body>" in text
    assert "\n" in text


def test_get_text_wraps_request_errors() -> None:
    client = WeatherClient(
        retries=0,
        session=FakeSession({"example.com": requests.ConnectionError("offline")}),
    )

    with pytest.raises(NetworkError, match="测试失败"):
        client.get_text("https://example.com", error_context="测试失败")
