#!/usr/bin/python
# -*- coding: utf-8 -*-
# Author: Whitejoce

import sys
import re
import time
import json
import requests
import bs4
import argparse

# 通用请求头（headers 合并改动）
headers = {
    'Referer': "http://www.weather.com.cn",
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0'
}

# 改动 1：定义 debug_mode，用于获取状态码
def debug_mode(city):
    """
    Debug Mode: 检测指定城市的所有相关 URL 的状态码。
    """
    urls = [
        f"http://toy1.weather.com.cn/search?city={city}",
        f"http://d1.weather.com.cn/weather_index/{city}.html",
        f"http://d1.weather.com.cn/dingzhi/{city}.html"
    ]
    results = []  # 用于存储状态码结果

    for url in urls:
        try:
            response = requests.get(url, headers=headers, timeout=10)
            # 打印状态码并存储结果
            print(f"URL: {url}, Status Code: {response.status_code}")
            results.append({"url": url, "status_code": response.status_code})
        except Exception as e:
            # 捕获异常并记录
            print(f"Error fetching URL: {url}, Exception: {e}")
            results.append({"url": url, "error": str(e)})

    # 将结果保存到文件
    with open("debug_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    print("Debug results saved to debug_results.json")

# 获取天气数据的主要逻辑（未改动，保持现状）
def main_weather_process(city):
    """
    获取并打印天气信息的主要逻辑（省略部分细节）。
    """
    print(f"Fetching weather data for city: {city}...")
    # 此处为现有获取天气数据的完整逻辑
    pass

if __name__ == "__main__":
    # 改动 2：支持命令行参数解析
    parser = argparse.ArgumentParser(description="Weather Script with Debug Mode")
    parser.add_argument("--debug", action="store_true", help="启用 Debug 模式，仅检查状态码")
    parser.add_argument("--city", type=str, default="101280601", help="城市代码 (默认: 广州)")
    args = parser.parse_args()

    # 改动 3：根据参数选择运行模式
    if args.debug:
        debug_mode(args.city)
    else:
        main_weather_process(args.city)
