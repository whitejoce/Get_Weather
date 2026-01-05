#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Weather information fetcher for Chinese cities.

This script fetches weather information from Chinese weather websites
and displays it in a formatted way.

Author: Whitejoce
License: MIT
"""

import argparse
import json
import logging
import re
import sys
import time
from typing import Dict, List, Optional, Tuple

import bs4
import requests

# Constants
DEFAULT_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0'
REQUEST_TIMEOUT = 10  # seconds
RETRY_TIMEOUT = 15  # seconds for retry attempts

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_headers(cookie: Optional[str] = None, referer: Optional[str] = None) -> Dict[str, str]:
    """
    Create HTTP headers for requests.
    
    Args:
        cookie: Optional cookie string to include
        referer: Optional referer URL to include
        
    Returns:
        Dictionary of HTTP headers
    """
    headers = {
        'User-Agent': DEFAULT_USER_AGENT
    }
    if cookie:
        headers['Cookie'] = cookie
    if referer:
        headers['Referer'] = referer
    return headers


def get_CityName() -> Tuple[str, str]:
    """
    Automatically detect the user's city based on their IP address.
    
    Returns:
        Tuple of (city_name, city_code). Returns empty strings if detection fails.
        
    Raises:
        SystemExit: If network requests fail after retry
    """
    timestamp = str(int(round(time.time() * 1000)))
    url = f'http://wgeo.weather.com.cn/ip/?_={timestamp}'
    
    try:
        res = requests.get(url, headers=create_headers(), timeout=REQUEST_TIMEOUT)
        res.raise_for_status()
    except requests.RequestException as e:
        logger.warning(f"首次请求失败: {e}")
        logger.info("正在进行网络自检并重试")
        try:
            res = requests.get(
                url, 
                headers=create_headers('', 'http://www.weather.com.cn'),
                timeout=RETRY_TIMEOUT
            )
            res.raise_for_status()
        except requests.RequestException as retry_error:
            logger.error(f"重试失败: {retry_error}")
            print(f" [!]无法从相关网站获得请求，退出脚本")
            sys.exit(1)

    res_text = res.content.decode('utf-8')
    City = re.findall(r'addr="(.*?)"', res_text)
    
    if not City:
        logger.warning('未自动匹配到地区信息')
        print(' [!] 未自动匹配到你所在地的地区信息')
        return "", ""
    
    CityName = "".join(City).split(',')[-1]
    code = re.findall(r'id="(.*?)"', res_text)
    
    if code:
        return CityName, code[0]
    return CityName, ""


def get_city_code(city: str) -> str:
    """
    Get the city code for a given city name.
    
    Args:
        city: Name of the city in Chinese
        
    Returns:
        City code (AREAID)
        
    Raises:
        SystemExit: If city cannot be found
    """
    try:
        url = "https://j.i8tq.com/weather2020/search/city.js"
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        raw_content = response.text
        raw_data = json.loads(raw_content[15:])
        
        def find_city_by_name(name: str, data: dict) -> Optional[dict]:
            """Recursively search for city by name in nested dictionary."""
            for k, v in data.items():
                if k == "NAMECN" and v == name:
                    return data
                if isinstance(v, dict):
                    result = find_city_by_name(name, v)
                    if result:
                        return result
            return None
        
        city_data = find_city_by_name(city, raw_data)
        if city_data and 'AREAID' in city_data:
            return city_data['AREAID']
        
        logger.error(f'未能找到城市 "{city}" 的信息')
        print(f' [!] 错误，未能找到该地区信息: {city}')
        print(" [#] 退出脚本")
        sys.exit(1)
    except requests.RequestException as e:
        logger.error(f'请求城市代码失败: {e}')
        print(f' [!] 网络请求失败: {e}')
        print(" [#] 退出脚本")
        sys.exit(1)
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        logger.error(f'解析城市数据失败: {e}')
        print(f' [!] 数据解析错误')
        print(" [#] 退出脚本")
        sys.exit(1)


def get_weaPage(url: str, headers: Dict[str, str]) -> str:
    """
    Fetch and parse a weather page.
    
    Args:
        url: URL to fetch
        headers: HTTP headers to use
        
    Returns:
        Prettified HTML content
        
    Raises:
        requests.RequestException: If request fails
    """
    res = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
    res.raise_for_status()
    s = res.content.decode('utf-8')
    bs = bs4.BeautifulSoup(s, "html.parser")
    html = bs.prettify()
    return html


def CheckInput(InputString: str) -> bool:
    """
    Check if input string contains invalid characters for a city name.
    
    Args:
        InputString: User input to validate
        
    Returns:
        True if input is invalid (contains digits, spaces, or English letters), False otherwise
    """
    if any(char.isdigit() for char in InputString) or InputString.isspace():
        return True
    match = re.search(r'[a-zA-Z]+$', InputString)
    if match:
        return True
    return False


def get_weather(City_code: str) -> str:
    """
    Fetch and format weather information for a given city code.
    
    Args:
        City_code: The city code to fetch weather for
        
    Returns:
        Formatted weather information string
        
    Raises:
        requests.RequestException: If any HTTP request fails
        json.JSONDecodeError: If JSON parsing fails
    """
    # Generate timestamp (13 digits, milliseconds)
    timestamp = str(int(round(time.time() * 1000)))
    
    # Fetch main weather data
    port = f"http://d1.weather.com.cn/weather_index/{City_code}.html?_={timestamp}"
    html = get_weaPage(port, create_headers('', 'http://www.weather.com.cn'))
    wea_list_all = html.split("var")

    # Fetch temperature data
    temp_port = f"http://d1.weather.com.cn/dingzhi/{City_code}.html?_={timestamp}"
    temp_html = get_weaPage(temp_port, create_headers('', 'http://www.weather.com.cn'))

    # Parse temperature data
    temp_data = re.findall(r'"weatherinfo":{(.*?)}', temp_html)
    temp_json_str = '{' + temp_data[0] + '}'
    temp_json = json.loads(temp_json_str)

    maxtemp = temp_json['temp']
    mintemp = temp_json['tempn']

    # Parse dataSK (current weather data)
    wea_list3 = re.findall(r' dataSK ={(.*?)}', wea_list_all[3])
    wea_list3_str = '{' + wea_list3[0] + '}'
    wea_list3_json = json.loads(wea_list3_str)

    # Extract weather data
    city_en = wea_list3_json['nameen']
    cityname = wea_list3_json['cityname']
    wea_now = wea_list3_json['weather']
    temp_now = wea_list3_json['temp']
    wet = wea_list3_json['SD']
    update = wea_list3_json['time']
    aqi = wea_list3_json['aqi']
    aqi_pm25 = wea_list3_json['aqi_pm25']
    date = wea_list3_json['date']

    # Parse dataZS (lifestyle indices)
    wea_list4 = re.findall(r'"zs":{(.*?)}', wea_list_all[4])
    wea_list4_str = '{' + wea_list4[0] + '}'
    wea_list4_json = json.loads(wea_list4_str)
    umbrella = wea_list4_json['ys_des_s']

    # Fetch QWeather data
    qwea_url = f"https://www.qweather.com/weather/{city_en}-{City_code}.html"
    qwea_html = get_weaPage(qwea_url, create_headers())

    wea_comment = re.findall(
        r'<div class="current-abstract">(.*?)</div>', qwea_html, re.S)
    wea_comment = "".join(wea_comment).strip()
    
    aqi_level = re.findall(
        r'<p class="city-air-chart__txt text-center">(.*?)</p>', qwea_html, re.S)
    aqi_level = aqi_level[0].strip() if aqi_level else "未知"

    # Format weather text
    weather_text = ''' {0}

 ===================================
 定位城市:  {1}
 实时天气:  {2}
 体感温度:  {3}℃
 温度区间:  {4} ~ {5}
 空气湿度:  {6}
 空气质量:  {7}({8}),PM2.5: {9}
 雨具携带:  {10}
 [更新时间: {11} {12}]
 ==================================='''.format(wea_comment, cityname, wea_now, temp_now, maxtemp,
                                               mintemp, wet, aqi, aqi_level, aqi_pm25, umbrella, date, update)

    # alarmDZ
    # -----------------------------------------------------
    weather_text += "\n".join(weather_alarm(wea_list_all[2]))
    #print(weather_text)
    return weather_text

def weather_alarm(alarm_list):
    json_str = re.search(r"alarmDZ\s*=\s*(\{.*\});", alarm_list, re.DOTALL).group(1)
    alarmDZ = json.loads(json_str)
    if alarmDZ["w"] == []:
        return
    yield ("\n [!]气象部门发布" + str(len(alarmDZ["w"])) + "则预警,请注意:")
    for alarm, id in enumerate(alarmDZ["w"]):
        content = id["w9"].replace("：", ":\n ", 1)
        yield (" [" + str(alarm + 1) + "]" + content)
        yield (
            " \t[=]详情: https://www.weather.com.cn/alarm/newalarmcontent.shtml?file="
            + id["w11"]
        )

def main_weather_process(output=0):
    try:
        address, code = get_CityName()
        if len(address) == 0:
            address = input(" [?] 请手动输入所在地（例：广州）[输入为空即退出]：")
            if address == "":
                print(" [#] 退出脚本")
                sys.exit(1)
            else:
                if CheckInput(address):
                    print(" [!]检测非地名字符，退出脚本")
                    sys.exit(1)
                else:
                    print(" [+] 使用手动输入定位位置："+address)
                    code = get_city_code(address)
        else:
            print(" [+] 自动定位位置："+address)

        try:
            weather_text = get_weather(code)
            if output == 0:
                print("\n"+weather_text+"\n")
                # os.system("pause")
            elif output == 1:
                from tkinter import Tk, Text, INSERT
                windows = Tk()
                windows.title("GetWeather")
                text1 = Text(windows)
                text1.insert(INSERT, weather_text)
                text1.pack()
                windows.mainloop()
        except Exception as Error:
            print(' [!] 未能找到该地区的天气信息')
            print(" [#] 退出脚本")
            raise Error
            sys.exit()
    except Exception:
        raise


def debug_mode(city):
    """
    Debug Mode: 检测指定城市的所有相关 URL 的状态码。
    """
    urls = [
        f"https://j.i8tq.com/weather2020/search/city.js",
        f"http://d1.weather.com.cn/weather_index/{city}.html",
        f"http://d1.weather.com.cn/dingzhi/{city}.html"
    ]
    results = []  # 用于存储状态码结果

    for url in urls:
        try:
            response = requests.get(url, headers=create_headers(), timeout=10)
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

if __name__ == '__main__':
    
    # 改动 2：支持命令行参数解析
    parser = argparse.ArgumentParser(description="Weather Script with Debug Mode")
    parser.add_argument("--debug", action="store_true", help="启用 Debug 模式，仅检查状态码")
    parser.add_argument("--city", type=str, default="101280601", help="城市代码 (默认: 广州)")
    parser.add_argument("--output", type=int, default=0, help="输出模式，0为shell输出，1为窗口输出(窗口仅输出天气信息)")
    args = parser.parse_args()

    # 改动 3：根据参数选择运行模式
    if args.debug:
        debug_mode(args.city)
    else:
        output = args.output
        main_weather_process(output)
