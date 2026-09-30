#!/usr/bin/python
# _*_coding: utf-8 _*_
# Coder:Whitejoce

import datetime
import json
import re
import sys
import time
from dataclasses import dataclass
from typing import Dict, List, Optional

import argparse

import bs4
import httpx
'''
TODO:
1. 输出使用Rich库美化
2. 支持命令行参数解析

要有很多f-string

3. 选项解析还没完成
'''


DEFAULT_TIMEOUT = 10


def parse_first_number(text: str) -> Optional[float]:
    match = re.search(r"-?\d+(?:\.\d+)?", str(text))
    if not match:
        return None
    try:
        return float(match.group(0))
    except ValueError:
        return None


def get_temp_style(temp_text: str) -> Optional[str]:
    value = parse_first_number(temp_text)
    if value is None:
        return None
    if value <= 0:
        return "cold"
    if value <= 10:
        return "cool"
    if value <= 20:
        return "mild"
    if value <= 28:
        return "warm"
    if value <= 35:
        return "hot"
    return "very_hot"


def get_aqi_style(aqi_text: str) -> Optional[str]:
    value = parse_first_number(aqi_text)
    if value is None:
        return None
    if value <= 50:
        return "excellent"
    if value <= 100:
        return "good"
    if value <= 150:
        return "light_pollution"
    if value <= 200:
        return "moderate_pollution"
    if value <= 300:
        return "heavy_pollution"
    return "severe_pollution"


def style_text(text: str, style_key: Optional[str], color_mode: str) -> str:
    if not style_key or color_mode == "none":
        return text

    ansi_map = {
        "cold": "94",
        "cool": "96",
        "mild": "92",
        "warm": "93",
        "hot": "33",
        "very_hot": "91",
        "excellent": "92",
        "good": "93",
        "light_pollution": "33",
        "moderate_pollution": "91",
        "heavy_pollution": "95",
        "severe_pollution": "31",
    }

    rich_map = {
        "cold": "bright_blue",
        "cool": "cyan",
        "mild": "green",
        "warm": "yellow",
        "hot": "orange3",
        "very_hot": "bright_red",
        "excellent": "green",
        "good": "yellow",
        "light_pollution": "orange3",
        "moderate_pollution": "red",
        "heavy_pollution": "magenta",
        "severe_pollution": "dark_red",
    }

    if color_mode == "ansi":
        code = ansi_map.get(style_key)
        return f"\033[{code}m{text}\033[0m" if code else text

    if color_mode == "rich":
        color = rich_map.get(style_key)
        return f"[{color}]{text}[/{color}]" if color else text

    return text


@dataclass
class WeatherSnapshot:
    city_cn: str
    city_en: str
    description: str
    temp_now: str
    humidity: str
    date: str
    update_time: str
    max_temp: str
    min_temp: str


@dataclass
class AirQuality:
    aqi: str
    level: str
    pm25: str


@dataclass
class WeatherReport:
    summary: str
    snapshot: WeatherSnapshot
    air_quality: AirQuality
    umbrella: str
    alarms: List[str]

    def as_text(self, color_mode: str = "none") -> str:
        temp_now = style_text(self.snapshot.temp_now, get_temp_style(self.snapshot.temp_now), color_mode)
        max_temp = style_text(self.snapshot.max_temp, get_temp_style(self.snapshot.max_temp), color_mode)
        min_temp = style_text(self.snapshot.min_temp, get_temp_style(self.snapshot.min_temp), color_mode)
        aqi_style = get_aqi_style(self.air_quality.aqi)
        aqi_level = style_text(self.air_quality.level, aqi_style, color_mode)
        aqi_value = style_text(self.air_quality.aqi, aqi_style, color_mode)
        pm25_value = style_text(self.air_quality.pm25, aqi_style, color_mode)

        lines = [
            f"● 根据天气查询结果，今天{self.snapshot.city_cn}的天气情况如下：",
            "",
            " 今日天气概况：",
            f" - 🌤️ 天气：{self.snapshot.description}",
            f" - 🌡️ 当前温度：{temp_now}℃",
            f" - 📊 温度范围：{max_temp} ~ {min_temp}",
            f" - 💧 湿度：{self.snapshot.humidity}",
            f" - 🌬️ 空气质量：{aqi_level}（AQI: {aqi_value}，PM2.5: {pm25_value}）",
            "",
            " 生活建议：",
            f" - ☂️ 雨具携带：{self.umbrella}",
            f" - 📝 天气概况：{self.summary}",
            "",
            f" 更新时间：{self.snapshot.date} {self.snapshot.update_time}",
        ]
        # lines = [
        #     f" {self.summary}",
        #     "\n ===================================",
        #     f" 定位城市:  {self.snapshot.city_cn}",
        #     f" 实时天气:  {self.snapshot.description}",
        #     f" 体感温度:  {self.snapshot.temp_now}℃",
        #     f" 温度区间:  {self.snapshot.max_temp} ~ {self.snapshot.min_temp}",
        #     f" 空气湿度:  {self.snapshot.humidity}",
        #     f" 空气质量:  {self.air_quality.aqi}({self.air_quality.level}),PM2.5: {self.air_quality.pm25}",
        #     f" 雨具携带:  {self.umbrella}",
        #     f" [更新时间: {self.snapshot.date} {self.snapshot.update_time}]",
        #     " ===================================",
        # ]
        if self.alarms:
            lines.extend(self.alarms)
        return "\n".join(lines)


def create_headers(cookie=None, referer=None):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0'
    }
    if cookie:
        headers['Cookie'] = cookie
    if referer:
        headers['Referer'] = referer
    return headers


def http_get(url, **kwargs):
    """统一请求入口: 对齐 requests 默认行为(httpx 默认不跟随重定向)。"""
    return httpx.get(url, follow_redirects=True, **kwargs)

def dumpResponse(response):
    with open("response.html", "w", encoding="utf-8") as f:
        f.write(response)


def fetch_text(url: str, headers: Optional[Dict[str, str]] = None, *, timeout: int = DEFAULT_TIMEOUT) -> str:
    response = http_get(url, headers=headers or create_headers(), timeout=timeout)
    response.raise_for_status()
    # 上游接口均为 UTF-8; httpx 无 charset 时默认按 UTF-8 解码(errors=replace),
    # 替代 requests 时代的 iso-8859-1/apparent_encoding 处理
    return response.text


def extract_json_block(text: str, var_name: str) -> Optional[dict]:
    assign_pattern = re.compile(rf"{re.escape(var_name)}\s*=\s*", re.MULTILINE)
    match = assign_pattern.search(text)
    if not match:
        return None
    start = text.find("{", match.end())
    if start == -1:
        return None
    depth = 0
    for index in range(start, len(text)):
        char = text[index]
        if char == '{':
            depth += 1
        elif char == '}':
            depth -= 1
            if depth == 0:
                return json.loads(text[start:index + 1])
    return None


def parse_qweather_summary(html: str) -> tuple[str, str]:
    soup = bs4.BeautifulSoup(html, "html.parser")
    summary_node = soup.select_one("div.current-abstract")
    summary = summary_node.get_text(strip=True) if summary_node else ""
    aqi_node = soup.select_one("p.city-air-chart__txt.text-center")
    aqi_level = aqi_node.get_text(strip=True) if aqi_node else ""
    return summary, aqi_level

def get_CityName(city_code="",city_name=""):
    timestamp = str(int(round(time.time() * 1000)))
    # https://wgeo.weather.com.cn/ip/?_=1776061426203
    url = 'http://wgeo.weather.com.cn/ip/?_='+timestamp
    try:
        # Magic Cookie: f_city=%E6%9D%AD%E5%B7%9E%7C621005320%7C
        res = http_get(url, headers=create_headers(r'f_city=%E6%9D%AD%E5%B7%9E%7C621005320%7C', 'http://www.weather.com.cn'), timeout=DEFAULT_TIMEOUT)
    except:
        print(" [!]正在进行网络自检并重试")
        try:
            res = http_get(url, headers=create_headers(r'f_city=%E6%9D%AD%E5%B7%9E%7C621005320%7C', 'http://www.weather.com.cn'), timeout=DEFAULT_TIMEOUT)
        except:
            print(" [!]无法从相关网站获得请求(请求总时长：25s)，退出脚本")
            sys.exit(1)

    res = res.content.decode('utf-8')
    City = re.findall('addr="(.*?)"', res)
    # print(res)
    if City == []:
        print(' [!] 未自动匹配到你所在地的地区信息')
    else:
        CityName = "".join(City).split(',')[-1]
        #ip=re.findall('ip:"(.*?)"', res)
        code = re.findall('id="(.*?)"', res)
        return CityName, code[0]
    return "", ""


def find_city_by_name(name, data):
    """在城市列表 JSON 中递归查找 "NAMECN" 为 name 的城市数据块。"""
    for k, v in data.items():
        if k == "NAMECN" and v == name:
            return data
        if isinstance(v, dict):
            result = find_city_by_name(name, v)
            if result:
                return result
    return None


def search_city_code(city):
    """优化 C: 轻量城市搜索接口(约159B), 精确匹配返回城市代码, 失败/未命中返回 None。

    响应形如: [{"ref":"101210301~zhejiang~嘉兴~Jiaxing~嘉兴~Jiaxing~573~314000~JX~浙江"}, ...]
    ~ 分隔的第3段为城市/区县名, 需过滤模糊命中(如"嘉兴路街道")。
    """
    try:
        res = http_get(
            "http://toy1.weather.com.cn/search",
            params={"cityname": city},
            headers=create_headers('', 'http://www.weather.com.cn'),
            timeout=DEFAULT_TIMEOUT,
        )
        res.raise_for_status()
        text = res.content.decode("utf-8", errors="replace")
    except Exception:
        return None
    for ref in re.findall(r'"ref":"([^"]+)"', text):
        fields = ref.split("~")
        if len(fields) > 2 and fields[2] == city:
            return fields[0]
    return None


def _city_code_from_list(city, raw_content):
    """从完整城市列表文本(city.js)中查找城市代码, 找不到时退出脚本。"""
    try:
        json_start = raw_content.find("{")
        if json_start == -1:
            raise ValueError("城市列表数据格式异常")
        raw_data = json.loads(raw_content[json_start:])
        city_data = find_city_by_name(city, raw_data)
        if not city_data:
            raise ValueError(f"未找到城市: {city}")
        return city_data['AREAID']
    except Exception as Error:
        print(' [!] 错误，未能找到该地区信息')
        print(" [#] 退出脚本")
        #raise Error
        sys.exit()


def get_city_code(city, raw_content=None):
    """城市名 -> 城市代码。

    优化 C: 优先使用轻量搜索接口(约159B); 失败或未命中时回退完整城市列表 city.js(约345KB)。
    raw_content 可传入本地保存的城市列表文本, 跳过网络(离线测试用)。
    """
    if raw_content is not None:
        return _city_code_from_list(city, raw_content)

    code = search_city_code(city)
    if code:
        return code

    try:
        raw_content = http_get(
            "https://j.i8tq.com/weather2020/search/city.js", timeout=15
        ).text
    except Exception as Error:
        print(' [!] 错误，未能找到该地区信息')
        print(" [#] 退出脚本")
        sys.exit()
    return _city_code_from_list(city, raw_content)


def CheckInput(InputString):
    if any(char.isdigit() for char in InputString) or InputString.isspace():
        return True
    match = re.search('[a-zA-Z]+$', InputString)
    if match:
        return True
    return False

# ---------------- 摘要本地合成(优化B: 替代和风页面摘要) ----------------
# 句式规律来自 30 城采样分析, 详见 test/README.md「和风摘要句式」。

WEATHER_TEXT_BY_CODE = {
    "00": "晴", "01": "多云", "02": "阴", "03": "阵雨", "04": "雷阵雨",
    "05": "雷阵雨伴冰雹", "06": "雨夹雪", "07": "小雨", "08": "中雨",
    "09": "大雨", "10": "暴雨", "11": "大暴雨", "12": "阵雪", "13": "小雪",
    "14": "中雪", "15": "大雪", "16": "暴雪", "17": "雾", "18": "冻雨",
    "19": "沙尘暴", "20": "小到中雨", "21": "中到大雨", "22": "大到暴雨",
    "23": "暴雨到大暴雨", "24": "大暴雨到特大暴雨", "25": "小到中雪",
    "26": "中到大雪", "27": "大到暴雪", "28": "浮尘", "29": "扬沙",
    "30": "强沙尘暴", "31": "霾", "53": "无",
}


def weather_text_from_code(code):
    """天气编码(00/01/.../31, 可带 d/n 前缀) -> 中文天气文本。"""
    return WEATHER_TEXT_BY_CODE.get(str(code).strip().lstrip("dn"), "")


def day_night_weather(index_html):
    """今日白天/夜晚天气文本。优先 cityDZ.weather(白天转夜晚), 回退 fc[0].fa/fb 编码。"""
    citydz = (extract_json_block(index_html, "cityDZ") or {}).get("weatherinfo", {})
    parts = [p for p in str(citydz.get("weather", "")).split("转") if p]
    if len(parts) >= 2:
        return parts[0], parts[-1]
    if len(parts) == 1:
        return parts[0], parts[0]
    fc0 = ((extract_json_block(index_html, "fc") or {}).get("f") or [{}])[0]
    day = weather_text_from_code(fc0.get("fa", ""))
    night = weather_text_from_code(fc0.get("fb", ""))
    return day, night


def aqi_level_text(aqi_value):
    """AQI 数值 -> 国标等级(优/良/轻度污染/...)。"""
    value = parse_first_number(aqi_value)
    if value is None:
        return ""
    if value <= 50:
        return "优"
    if value <= 100:
        return "良"
    if value <= 150:
        return "轻度污染"
    if value <= 200:
        return "中度污染"
    if value <= 300:
        return "重度污染"
    return "严重污染"


def air_phrase(aqi_value):
    """AQI 数值 -> 摘要用空气评价(30 城采样: 优->不错, 良->一般)。"""
    value = parse_first_number(aqi_value)
    if value is None:
        return ""
    if value <= 50:
        return "不错"
    if value <= 100:
        return "一般"
    if value <= 150:
        return "较差"
    return "很差"


def wind_phrase(ws_text):
    """风力文本(如 '2级'/'<3级') -> 摘要用风表述(有风/风很大/无)。"""
    value = parse_first_number(ws_text)
    if value is None:
        return ""
    if value >= 4:
        return "风很大"
    if value >= 2:
        return "有风"
    return ""


def extract_fc40(text):
    """从 calendar_new 响应中提取 fc40 数组(35 天, 近 5 天为实测)。"""
    m = re.search(r"var\s+fc40\s*=\s*", text)
    if not m:
        return None
    start = text.find("[", m.end())
    if start == -1:
        return None
    depth = 0
    for i in range(start, len(text)):
        char = text[i]
        if char == "[":
            depth += 1
        elif char == "]":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start:i + 1])
                except ValueError:
                    return None
    return None


def fetch_calendar_fc40(city_code, ym=None):
    """获取 calendar_new 的 fc40(当月文件覆盖上月底~下月初)。失败返回 None。"""
    if ym is None:
        ym = time.strftime("%Y%m")
    url = f"http://d1.weather.com.cn/calendar_new/{ym[:4]}/{city_code}_{ym}.html"
    try:
        text = fetch_text(url, create_headers('', 'http://www.weather.com.cn'))
    except Exception:
        return None
    return extract_fc40(text)


def find_yesterday_obs(fc40, today=None):
    """在 fc40 中找昨日实测条目(cla=obs, 含 maxobs/minobs)。today 可传 YYYYMMDD 用于测试。"""
    if not fc40:
        return None
    if today:
        day = datetime.datetime.strptime(today, "%Y%m%d").date()
    else:
        day = datetime.date.today()
    yesterday = (day - datetime.timedelta(days=1)).strftime("%Y%m%d")
    for entry in fc40:
        if entry.get("date") == yesterday and entry.get("maxobs") and entry.get("minobs"):
            return entry
    return None


def build_temp_compare(today_max, yesterday_max):
    """今日最高温 vs 昨日实测最高温 -> '温度和昨天差不多'/'比昨天热一些'等。"""
    a = parse_first_number(today_max)
    b = parse_first_number(yesterday_max)
    if a is None or b is None:
        return ""
    diff = int(a) - int(b)
    if abs(diff) <= 1:
        return "温度和昨天差不多"
    degree = "很多" if abs(diff) >= 5 else "一些"
    if diff > 0:
        return f"比昨天{'热' if a >= 25 else '暖和'}{degree}"
    return f"比昨天凉爽{degree}"


def build_summary(data_sk, index_html, yesterday_obs):
    """本地合成一句话天气摘要(句式对齐和风摘要, 规律见 test/README.md)。"""
    day_w, night_w = day_night_weather(index_html)

    def you(text):
        # 采样规律: 降水/雾霾等加"有"前缀, 晴/多云/阴不加
        return text if text in ("晴", "多云", "阴", "") else f"有{text}"

    if day_w and night_w and day_w != night_w:
        weather_seg = f"今天白天{you(day_w)}，夜晚{you(night_w)}"
    elif day_w or night_w:
        weather_seg = f"今天{you(day_w or night_w)}"
    else:
        weather_seg = ""

    fc0 = ((extract_json_block(index_html, "fc") or {}).get("f") or [{}])[0]
    compare = ""
    if yesterday_obs:
        compare = build_temp_compare(fc0.get("fc", ""), yesterday_obs.get("maxobs", ""))

    temp_now = parse_first_number(data_sk.get("temp", ""))
    now_seg = f"现在{int(temp_now)}°" if temp_now is not None else ""
    wind = wind_phrase(data_sk.get("WS", ""))
    air_word = air_phrase(data_sk.get("aqi", ""))
    air = f"空气{air_word}" if air_word else ""

    segs = [seg for seg in (weather_seg, compare, now_seg, wind, air) if seg]
    return "，".join(segs) + "。"


def get_weather(city_code: str) -> WeatherReport:
    timestamp = str(int(round(time.time() * 1000)))
    base_headers = create_headers('', 'http://www.weather.com.cn')

    # 优化 A: 温度区间直接取 weather_index 内 fc[0](今天, fc=最高/fd=最低),
    # 数据与已移除的 dingzhi 请求一致(跨城市验证), 少一次请求
    index_html = fetch_text(
        f"http://d1.weather.com.cn/weather_index/{city_code}.html?_={timestamp}",
        base_headers,
    )
    data_sk = extract_json_block(index_html, "dataSK") or {}
    data_zs = extract_json_block(index_html, "dataZS") or {}
    alarm_dz = extract_json_block(index_html, "alarmDZ") or {}
    fc_days = (extract_json_block(index_html, "fc") or {}).get("f") or []
    today = fc_days[0] if fc_days else {}

    # 优化 B: 摘要本地合成, 不再请求和风页面(90KB); 昨日实测取自 calendar_new
    fc40 = fetch_calendar_fc40(city_code)
    yesterday_obs = find_yesterday_obs(fc40)
    summary = build_summary(data_sk, index_html, yesterday_obs)

    city_en = data_sk.get("nameen", "")
    temp_now = data_sk.get("temp", "")
    snapshot = WeatherSnapshot(
        city_cn=data_sk.get("cityname", ""),
        city_en=city_en,
        description=data_sk.get("weather", ""),
        temp_now=temp_now,
        humidity=data_sk.get("SD", ""),
        date=data_sk.get("date", ""),
        update_time=data_sk.get("time", ""),
        max_temp=f"{today.get('fc', '').rstrip('℃')}℃" if today.get("fc") else temp_now,
        min_temp=f"{today.get('fd', '').rstrip('℃')}℃" if today.get("fd") else temp_now
    )

    air_quality = AirQuality(
        aqi=data_sk.get("aqi", ""),
        level=aqi_level_text(data_sk.get("aqi", "")) or data_sk.get("aqi", ""),
        pm25=data_sk.get("aqi_pm25", ""),
    )

    umbrella_info = data_zs.get("zs", {}).get("ys_des_s", "")
    alarms = build_alarm_messages(alarm_dz)

    return WeatherReport(
        summary=summary or snapshot.description,
        snapshot=snapshot,
        air_quality=air_quality,
        umbrella=umbrella_info,
        alarms=alarms,
    )

def build_alarm_messages(alarm_data: Optional[dict]) -> List[str]:
    if not alarm_data:
        return []

    alarms = alarm_data.get("w", [])
    if not alarms:
        return []

    messages = ["", f" [!]气象部门发布{len(alarms)}则预警,请注意:"]
    for index, item in enumerate(alarms, start=1):
        content = item.get("w9", "").replace("：", ":\n ", 1)
        messages.append(f" [{index}]{content}")
        detail = item.get("w11")
        if detail:
            messages.append(
                " \t[=]详情: https://www.weather.com.cn/alarm/newalarmcontent.shtml?file="
                + detail
            )
    return messages

def main_weather_process(output=0, city_name="", city_code="", color_mode="ansi"):
    try:
        if city_name:
            # 修复: --city-name 生效，校验后直接查城市代码，不再走自动定位
            if CheckInput(city_name):
                print(" [!]检测非地名字符，退出脚本")
                sys.exit(1)
            print(" [+] 使用指定城市：" + city_name)
            code = get_city_code(city_name)
        elif city_code:
            # 修复: --city-code 生效，直接使用城市代码查询
            print(" [+] 使用指定城市代码：" + city_code)
            code = city_code
        else:
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
            weather_report = get_weather(code)
            if output == 0:
                report_text = weather_report.as_text(color_mode=color_mode)
                if color_mode == "rich":
                    try:
                        from rich import print as rich_print
                        rich_print("\n" + report_text + "\n")
                    except ImportError:
                        print(" [!] 未安装 rich，已回退到 ANSI 配色输出")
                        print("\n" + weather_report.as_text(color_mode="ansi") + "\n")
                else:
                    print("\n" + report_text + "\n")
                # os.system("pause")
            elif output == 1:
                report_text = weather_report.as_text(color_mode="none")
                import tkinter as tk
                from tkinter import scrolledtext

                def create_weather_window(weather_text):
                    """创建并显示天气信息窗口"""
                    window = tk.Tk()
                    window.title("天气信息 - GetWeather")
                    window.geometry("600x500")
                    window.resizable(True, True)
                    
                    # 创建带滚动条的文本框
                    text_area = scrolledtext.ScrolledText(
                        window,
                        wrap=tk.WORD,
                        width=70,
                        height=25,
                        font=("Consolas", 10),
                        bg="#f0f0f0",
                        fg="#333333",
                        padx=10,
                        pady=10
                    )
                    text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
                    
                    # 插入天气信息
                    text_area.insert(tk.INSERT, weather_text)
                    text_area.config(state=tk.DISABLED)  # 设置为只读
                    
                    # 居中显示窗口
                    window.update_idletasks()
                    x = (window.winfo_screenwidth() // 2) - (window.winfo_width() // 2)
                    y = (window.winfo_screenheight() // 2) - (window.winfo_height() // 2)
                    window.geometry(f"+{x}+{y}")
                    
                    window.mainloop()
                create_weather_window(report_text)
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
    ym = time.strftime("%Y%m")
    urls = [
        "https://j.i8tq.com/weather2020/search/city.js",
        f"http://d1.weather.com.cn/weather_index/{city}.html",
        f"http://d1.weather.com.cn/calendar_new/{ym}/{city}_{ym}.html",
        "http://toy1.weather.com.cn/search?cityname=%E5%8C%97%E4%BA%AC",  # 北京: 搜索接口健康检查
    ]
    results = []  # 用于存储状态码结果

    for url in urls:
        try:
            # d1.weather.com.cn 必须携带 Referer, 否则返回 403
            response = http_get(url, headers=create_headers('', 'http://www.weather.com.cn'), timeout=10)
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
    parser.add_argument("--city-code", type=str, default=None, help="城市代码 (例: 101010100)；提供时跳过定位直接查询，与 --city-name 同时给出时后者优先")
    parser.add_argument("--city-name", type=str, help="城市名称 (例: 北京)，提供时跳过自动定位")
    parser.add_argument("--output", type=int, default=0, help="输出模式，0为shell输出，1为窗口输出(窗口仅输出天气信息)")
    parser.add_argument("--color-mode", type=str, choices=["none", "ansi", "rich"], default="ansi", help="终端配色模式: none/ansi/rich")
    args = parser.parse_args()

    # 改动 3：根据参数选择运行模式
    if args.debug:
        debug_mode(args.city_code or "101280601")
    else:
        output = args.output
        city_name = args.city_name
        city_code = args.city_code 
        color_mode = args.color_mode
        main_weather_process(output, city_name, city_code, color_mode)
