#!/usr/bin/python
# _*_coding: utf-8 _*_
# WeatherSkill: 天气查询 Skill，基于 GetWeather.py

import sys
import argparse

from GetWeather import (
    get_CityName,
    get_city_code,
    get_weather,
    CheckInput,
)


def query_weather(city_name: str) -> str:
    """
    查询指定城市的天气信息，返回天气文本。

    参数:
        city_name (str): 城市名称，例如 "北京"、"上海"

    返回:
        str: 格式化的天气信息文本；若查询失败则返回错误提示字符串。
    """
    if not city_name or not city_name.strip():
        return " [!] 城市名称不能为空"
    city_name = city_name.strip()
    if CheckInput(city_name):
        return " [!] 检测到非地名字符（不能包含数字、纯空格或英文字母），请输入有效的城市名称（例：北京）"
    try:
        code = get_city_code(city_name)
        weather_text = get_weather(code)
        return weather_text
    except SystemExit:
        return f" [!] 未能找到城市 '{city_name}' 的天气信息"
    except Exception as e:
        return f" [!] 查询天气时出错: {e}"


def query_weather_auto() -> str:
    """
    自动定位并查询当前所在城市的天气信息，返回天气文本。

    返回:
        str: 格式化的天气信息文本；若定位或查询失败则返回错误提示字符串。
    """
    try:
        address, code = get_CityName()
        if not address:
            return " [!] 无法自动定位城市，请使用 query_weather(city_name) 指定城市"
        weather_text = get_weather(code)
        return weather_text
    except SystemExit:
        return " [!] 未能获取当前位置的天气信息"
    except Exception as e:
        return f" [!] 查询天气时出错: {e}"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="天气查询 Skill — 通过城市名称查询实时天气"
    )
    parser.add_argument(
        "--city",
        type=str,
        default=None,
        help="城市名称 (例：北京)；不指定时自动定位",
    )
    args = parser.parse_args()

    if args.city:
        result = query_weather(args.city)
    else:
        result = query_weather_auto()

    print("\n" + result + "\n")
