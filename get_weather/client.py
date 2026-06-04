import json
import re
import time
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup

from .exceptions import CityNotFoundError, NetworkError, ParseError
from .parser import (
    extract_assigned_json,
    extract_object_after_key,
    parse_alarm_lines,
    parse_qweather_summary,
)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0"
)
WEATHER_REFERER = "http://www.weather.com.cn"
GEO_COOKIE = r"f_city=%E6%9D%AD%E5%B7%9E%7C621005320%7C"


def create_headers(
    cookie: str | None = None, referer: str | None = None
) -> dict[str, str]:
    headers = {"User-Agent": USER_AGENT}
    if cookie:
        headers["Cookie"] = cookie
    if referer:
        headers["Referer"] = referer
    return headers


class WeatherClient:
    def __init__(
        self,
        timeout: float = 10,
        retries: int = 1,
        session: requests.Session | None = None,
    ) -> None:
        self.timeout = timeout
        self.retries = retries
        self.session = session or requests.Session()

    def get_city_name(self) -> tuple[str, str]:
        timestamp = _timestamp_ms()
        url = f"http://wgeo.weather.com.cn/ip/?_={timestamp}"
        text = self.get_text(
            url,
            headers=create_headers(GEO_COOKIE, WEATHER_REFERER),
            error_context="自动定位城市失败",
        )

        city_match = re.search(r'addr="(.*?)"', text)
        code_match = re.search(r'id="(.*?)"', text)
        if not city_match or not code_match:
            return "", ""

        city_name = city_match.group(1).split(",")[-1]
        return city_name, code_match.group(1)

    def get_city_code(self, city: str) -> str:
        url = "https://j.i8tq.com/weather2020/search/city.js"
        raw_content = self.get_text(url, error_context="城市列表获取失败")
        json_start = raw_content.find("{")
        if json_start == -1:
            raise ParseError("城市列表数据格式异常")

        try:
            city_data, _ = json.JSONDecoder().raw_decode(raw_content[json_start:])
        except json.JSONDecodeError as exc:
            raise ParseError("城市列表 JSON 解析失败") from exc

        city_info = _find_city_by_name(city, city_data)
        if not city_info or not city_info.get("AREAID"):
            raise CityNotFoundError(f"未能找到城市 '{city}' 的地区信息")
        return str(city_info["AREAID"])

    def get_weather(
        self, city_code: str, dump_response_path: str | Path | None = None
    ) -> str:
        timestamp = _timestamp_ms()
        weather_url = (
            f"http://d1.weather.com.cn/weather_index/{city_code}.html?_={timestamp}"
        )
        weather_html = self.get_text(
            weather_url,
            headers=create_headers(referer=WEATHER_REFERER),
            error_context="天气详情获取失败",
        )
        if dump_response_path:
            Path(dump_response_path).write_text(weather_html, encoding="utf-8")

        temp_url = f"http://d1.weather.com.cn/dingzhi/{city_code}.html?_={timestamp}"
        temp_html = self.get_text(
            temp_url,
            headers=create_headers(referer=WEATHER_REFERER),
            error_context="温度区间获取失败",
        )

        temp_json = extract_object_after_key(temp_html, "weatherinfo")
        data_sk = extract_assigned_json(weather_html, "dataSK")
        data_zs = extract_assigned_json(weather_html, "dataZS").get("zs", {})

        city_en = _required(data_sk, "nameen", "城市英文名")
        qweather_url = f"https://www.qweather.com/weather/{city_en}-{city_code}.html"
        qweather_headers = create_headers(referer=qweather_url)
        qweather_html = self.get_text(
            qweather_url, headers=qweather_headers, error_context="天气摘要获取失败"
        )
        weather_comment, aqi_level = parse_qweather_summary(qweather_html)

        weather_text = _format_weather_text(
            weather_comment=weather_comment,
            data_sk=data_sk,
            data_zs=data_zs,
            temp_json=temp_json,
            aqi_level=aqi_level,
        )
        alarm_lines = parse_alarm_lines(weather_html)
        if alarm_lines:
            weather_text += "\n".join(alarm_lines)
        return weather_text

    def get_page(self, url: str, headers: dict[str, str] | None = None) -> str:
        text = self.get_text(url, headers=headers, error_context="页面获取失败")
        return BeautifulSoup(text, "html.parser").prettify()

    def debug_urls(
        self,
        city_code: str,
        output_file: str | Path | None = "debug_results.json",
    ) -> list[dict[str, Any]]:
        urls = [
            "https://j.i8tq.com/weather2020/search/city.js",
            f"http://d1.weather.com.cn/weather_index/{city_code}.html",
            f"http://d1.weather.com.cn/dingzhi/{city_code}.html",
        ]
        results: list[dict[str, Any]] = []

        for url in urls:
            try:
                response = self.session.get(
                    url,
                    headers=create_headers(),
                    timeout=self.timeout,
                )
                results.append({"url": url, "status_code": response.status_code})
            except requests.RequestException as exc:
                results.append({"url": url, "error": str(exc)})

        if output_file:
            Path(output_file).write_text(
                json.dumps(results, ensure_ascii=False, indent=4),
                encoding="utf-8",
            )
        return results

    def get_text(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        error_context: str = "请求失败",
    ) -> str:
        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                response = self.session.get(url, headers=headers, timeout=self.timeout)
                response.raise_for_status()
                return response.content.decode("utf-8", errors="replace")
            except requests.RequestException as exc:
                last_error = exc
                if attempt < self.retries:
                    time.sleep(0.5)

        raise NetworkError(f"{error_context}: {last_error}") from last_error


def _timestamp_ms() -> str:
    return str(int(round(time.time() * 1000)))


def _find_city_by_name(name: str, data: Any) -> dict[str, Any] | None:
    if isinstance(data, dict):
        if data.get("NAMECN") == name:
            return data
        for value in data.values():
            result = _find_city_by_name(name, value)
            if result:
                return result
    elif isinstance(data, list):
        for value in data:
            result = _find_city_by_name(name, value)
            if result:
                return result
    return None


def _required(data: dict[str, Any], key: str, label: str) -> str:
    value = data.get(key)
    if value in (None, ""):
        raise ParseError(f"缺少{label}字段: {key}")
    return str(value)


def _format_weather_text(
    weather_comment: str,
    data_sk: dict[str, Any],
    data_zs: dict[str, Any],
    temp_json: dict[str, Any],
    aqi_level: str,
) -> str:
    return """ {weather_comment}

 ===================================
 定位城市:  {cityname}
 实时天气:  {weather}
 体感温度:  {temp}℃
 温度区间:  {maxtemp} ~ {mintemp}
 空气湿度:  {humidity}
 空气质量:  {aqi}({aqi_level}),PM2.5: {aqi_pm25}
 雨具携带:  {umbrella}
 [更新时间: {date} {update}]
 ===================================""".format(
        weather_comment=weather_comment,
        cityname=_required(data_sk, "cityname", "城市名称"),
        weather=_required(data_sk, "weather", "实时天气"),
        temp=_required(data_sk, "temp", "实时温度"),
        maxtemp=_required(temp_json, "temp", "最高温度"),
        mintemp=_required(temp_json, "tempn", "最低温度"),
        humidity=_required(data_sk, "SD", "空气湿度"),
        aqi=_required(data_sk, "aqi", "空气质量"),
        aqi_level=aqi_level,
        aqi_pm25=_required(data_sk, "aqi_pm25", "PM2.5"),
        umbrella=data_zs.get("ys_des_s", "暂无雨具建议"),
        date=_required(data_sk, "date", "日期"),
        update=_required(data_sk, "time", "更新时间"),
    )
