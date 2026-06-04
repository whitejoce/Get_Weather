import json
import re
from typing import Any

from bs4 import BeautifulSoup

from .exceptions import ParseError


def extract_assigned_json(source: str, variable_name: str) -> dict[str, Any]:
    """Extract a JavaScript-assigned JSON object such as `var dataSK = {...};`."""
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


def parse_qweather_summary(html: str) -> tuple[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    summary_node = soup.find("div", class_="current-abstract")
    aqi_node = soup.find("p", class_="city-air-chart__txt")

    summary = summary_node.get_text(strip=True) if summary_node else ""
    aqi_level = aqi_node.get_text(strip=True) if aqi_node else "未知"
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
