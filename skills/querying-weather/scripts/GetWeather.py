import argparse
import html
import json
import re
import time
import urllib.error
import urllib.request
from typing import Any

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) "
    "Gecko/20100101 Firefox/66.0"
)
WEATHER_REFERER = "http://www.weather.com.cn"
GEO_COOKIE = r"f_city=%E6%9D%AD%E5%B7%9E%7C621005320%7C"


class WeatherSkillError(Exception):
    """Base exception for the standalone weather skill script."""


class CityNotFoundError(WeatherSkillError):
    """Raised when a city cannot be resolved to a weather area id."""


class NetworkError(WeatherSkillError):
    """Raised when an upstream request fails."""


class ParseError(WeatherSkillError):
    """Raised when upstream data cannot be parsed."""


def create_headers(cookie: str | None = None, referer: str | None = None) -> dict[str, str]:
    headers = {"User-Agent": USER_AGENT}
    if cookie:
        headers["Cookie"] = cookie
    if referer:
        headers["Referer"] = referer
    return headers


def get_text(
    url: str,
    headers: dict[str, str] | None = None,
    timeout: float = 10,
    retries: int = 1,
    error_context: str = "请求失败",
) -> str:
    headers = headers or create_headers()
    last_error: Exception | None = None

    for attempt in range(retries + 1):
        try:
            request = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.read().decode("utf-8", errors="replace")
        except (urllib.error.URLError, OSError) as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(0.5)

    raise NetworkError(f"{error_context}: {last_error}") from last_error


def CheckInput(input_string: str) -> bool:
    if not input_string or input_string.isspace():
        return True
    if any(char.isdigit() for char in input_string):
        return True
    return re.search(r"[a-zA-Z]+$", input_string) is not None


def get_CityName() -> tuple[str, str]:
    timestamp = _timestamp_ms()
    url = f"http://wgeo.weather.com.cn/ip/?_={timestamp}"
    text = get_text(
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


def get_city_code(city: str) -> str:
    raw_content = get_text(
        "https://j.i8tq.com/weather2020/search/city.js",
        error_context="城市列表获取失败",
    )
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


def get_weather(city_code: str) -> str:
    timestamp = _timestamp_ms()
    weather_url = f"http://d1.weather.com.cn/weather_index/{city_code}.html?_={timestamp}"
    weather_html = get_text(
        weather_url,
        headers=create_headers(referer=WEATHER_REFERER),
        error_context="天气详情获取失败",
    )

    temp_url = f"http://d1.weather.com.cn/dingzhi/{city_code}.html?_={timestamp}"
    temp_html = get_text(
        temp_url,
        headers=create_headers(referer=WEATHER_REFERER),
        error_context="温度区间获取失败",
    )

    temp_json = extract_object_after_key(temp_html, "weatherinfo")
    data_sk = extract_assigned_json(weather_html, "dataSK")
    data_zs = extract_assigned_json(weather_html, "dataZS").get("zs", {})

    city_en = _required(data_sk, "nameen", "城市英文名")
    qweather_url = f"https://www.qweather.com/weather/{city_en}-{city_code}.html"
    qweather_html = get_text(
        qweather_url,
        headers=create_headers(referer=qweather_url),
        error_context="天气摘要获取失败",
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


def query_weather(city_name: str) -> str:
    if not city_name or not city_name.strip():
        return " [!] 城市名称不能为空"

    city_name = city_name.strip()
    if CheckInput(city_name):
        return " [!] 检测到非地名字符（不能包含数字、纯空格或英文字母），请输入有效的城市名称（例：北京）"

    try:
        code = get_city_code(city_name)
        return get_weather(code)
    except WeatherSkillError:
        return f" [!] 未能找到城市 '{city_name}' 的天气信息"
    except Exception as exc:
        return f" [!] 查询天气时出错: {exc}"


def query_weather_auto() -> str:
    try:
        address, code = get_CityName()
        if not address:
            return " [!] 无法自动定位城市，请使用 query_weather(city_name) 指定城市"
        return get_weather(code)
    except WeatherSkillError:
        return " [!] 未能获取当前位置的天气信息"
    except Exception as exc:
        return f" [!] 查询天气时出错: {exc}"


def extract_assigned_json(source: str, variable_name: str) -> dict[str, Any]:
    assignment = re.search(rf"\b{re.escape(variable_name)}\s*=", source)
    if not assignment:
        raise ParseError(f"未找到 {variable_name} 数据")

    start = source.find("{", assignment.end())
    if start == -1:
        raise ParseError(f"{variable_name} 数据格式异常")

    end = _find_matching_brace(source, start)
    try:
        return json.loads(source[start : end + 1])
    except json.JSONDecodeError as exc:
        raise ParseError(f"{variable_name} JSON 解析失败") from exc


def extract_object_after_key(source: str, key: str) -> dict[str, Any]:
    match = re.search(rf'"{re.escape(key)}"\s*:', source)
    if not match:
        raise ParseError(f"未找到 {key} 数据")

    start = source.find("{", match.end())
    if start == -1:
        raise ParseError(f"{key} 数据格式异常")

    end = _find_matching_brace(source, start)
    try:
        return json.loads(source[start : end + 1])
    except json.JSONDecodeError as exc:
        raise ParseError(f"{key} JSON 解析失败") from exc


def parse_qweather_summary(source: str) -> tuple[str, str]:
    summary = _extract_tag_text(source, "div", "current-abstract")
    aqi_level = _extract_tag_text(source, "p", "city-air-chart__txt") or "未知"
    return summary, aqi_level


def parse_alarm_lines(source: str) -> list[str]:
    alarm_data = extract_assigned_json(source, "alarmDZ")
    alarms = alarm_data.get("w", [])
    if not alarms:
        return []

    lines = [f"\n [!]气象部门发布{len(alarms)}则预警,请注意:"]
    for index, alarm in enumerate(alarms, start=1):
        content = str(alarm.get("w9", "")).replace("：", ":\n ", 1)
        lines.append(f" [{index}]{content}")
        detail_file = alarm.get("w11")
        if detail_file:
            lines.append(
                " \t[=]详情: "
                "https://www.weather.com.cn/alarm/newalarmcontent.shtml?file="
                f"{detail_file}"
            )
    return lines


def _find_matching_brace(source: str, start: int) -> int:
    depth = 0
    in_string = False
    escaped = False

    for index in range(start, len(source)):
        char = source[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return index

    raise ParseError("JSON 对象括号不匹配")


def _extract_tag_text(source: str, tag: str, class_name: str) -> str:
    pattern = (
        rf"<{tag}\b(?=[^>]*class=[\"'][^\"']*{re.escape(class_name)}[^\"']*[\"'])"
        rf"[^>]*>(.*?)</{tag}>"
    )
    match = re.search(pattern, source, re.S)
    if not match:
        return ""
    text = re.sub(r"<[^>]+>", "", match.group(1))
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


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


def _timestamp_ms() -> str:
    return str(int(round(time.time() * 1000)))


def main() -> int:
    parser = argparse.ArgumentParser(description="天气查询 Skill")
    parser.add_argument(
        "--city",
        type=str,
        default=None,
        help="城市名称 (例：北京)；不指定时自动定位",
    )
    args = parser.parse_args()

    result = query_weather(args.city) if args.city else query_weather_auto()
    print("\n" + result + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
