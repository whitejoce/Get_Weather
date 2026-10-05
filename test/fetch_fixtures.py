#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""重新抓取 test/sample/ 下的本地请求样本（fixtures）。

用法:
    python test/fetch_fixtures.py            # 抓取全部样本
    python test/fetch_fixtures.py city.js    # 只抓取指定样本

若存在 .env(含 API_KEY=xxx)则会额外抓取华风爱科官方 API 样本(api_*.json)。
样本用于离线测试（pytest 不发网络请求）。请勿高频运行，遵守数据源网站使用规则。
"""

import re
import sys
import time
from pathlib import Path

import httpx

HERE = Path(__file__).resolve().parent
SAMPLES = HERE / "sample"

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0"
GEO_COOKIE = r"f_city=%E6%9D%AD%E5%B7%9E%7C621005320%7C"
WEATHER_REFERER = "http://www.weather.com.cn"
JIAXING = "101210301"  # 样本城市: 嘉兴


def create_headers(cookie=None, referer=None):
    headers = {"User-Agent": USER_AGENT}
    if cookie:
        headers["Cookie"] = cookie
    if referer:
        headers["Referer"] = referer
    return headers


def sample_urls():
    ts = str(int(round(time.time() * 1000)))
    now = time.localtime()
    ym = time.strftime("%Y%m", now)  # calendar_new 按月存放
    return [
        # (文件名, URL, headers)
        ("wgeo_ip.txt",
         f"http://wgeo.weather.com.cn/ip/?_={ts}",
         create_headers(GEO_COOKIE, WEATHER_REFERER)),
        ("toy1_search_jiaxing.txt",
         "http://toy1.weather.com.cn/search?cityname=%E5%98%89%E5%85%B4",  # cityname=嘉兴
         create_headers("", WEATHER_REFERER)),
        ("city.js",
         "https://j.i8tq.com/weather2020/search/city.js",
         create_headers()),
        ("weather_index_jiaxing.html",
         f"http://d1.weather.com.cn/weather_index/{JIAXING}.html?_={ts}",
         create_headers("", WEATHER_REFERER)),
        ("dingzhi_jiaxing.html",
         f"http://d1.weather.com.cn/dingzhi/{JIAXING}.html?_={ts}",
         create_headers("", WEATHER_REFERER)),  # 备用参考: 与 fc[0] 数据等价
        ("calendar_new_jiaxing.html",
         f"http://d1.weather.com.cn/calendar_new/{ym[:4]}/{JIAXING}_{ym}.html?_={ts}",
         create_headers("", WEATHER_REFERER)),  # 40天日历预报: fc40 数组(黄历/降水概率/温度)
        ("qweather_jiaxing.html",
         f"https://www.qweather.com/weather/jiaxing-{JIAXING}.html",
         create_headers()),  # 备用参考: 摘要句式对照
    ]


def fetch_one(url, headers):
    resp = httpx.get(url, headers=headers, timeout=15, follow_redirects=True)
    resp.raise_for_status()
    return resp.content.decode("utf-8", errors="replace")


def main(argv):
    wanted = set(argv[1:])
    ok, failed = [], []
    for name, url, headers in sample_urls():
        if wanted and name not in wanted:
            continue
        try:
            text = fetch_one(url, headers)
            path = SAMPLES / name
            path.write_text(text, encoding="utf-8")
            print(f"[+] 已保存 {name} ({len(text)} 字符)")
            ok.append(name)
        except Exception as exc:
            print(f"[!] 抓取失败 {name}: {exc}")
            failed.append(name)
    if failed:
        print(f"[#] 失败: {failed}")
        return 1
    return 0


# ---------- 华风爱科官方 API 样本(需要 .env 中的 API_KEY) ----------

OPENAPI_BASE = "https://openapi.weathercn.com"


def load_api_key():
    env_path = HERE.parent / ".env"
    if not env_path.exists():
        return None
    for line in env_path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\s*(?:WEATHERCN_API_KEY|API_KEY)\s*=\s*(\S+)", line)
        if m:
            return m.group(1)
    return None


def fetch_api_samples():
    """抓取官方 API 的嘉兴样本(7 个请求, 占用每日配额)。"""
    api_key = load_api_key()
    if not api_key:
        print("[#] 未找到 API_KEY, 跳过官方 API 样本")
        return 0
    print(f"[+] 从 .env 读取 key: {api_key[:4]}{'*' * 8}(掩码)")

    def call(name, path, **params):
        # 鉴权只能走查询参数: 网关实测不接受 X-Gw-API-Key/apikey 请求头(401/400)
        resp = httpx.get(
            f"{OPENAPI_BASE}{path}",
            params={"apikey": api_key, "language": "zh-cn", **params},
            timeout=20,
            follow_redirects=True,
        )
        resp.raise_for_status()
        (SAMPLES / name).write_text(resp.text, encoding="utf-8")
        print(f"[+] 已保存 {name} ({len(resp.text)} 字符)")
        return resp.json()

    loc_item = call("api_translate_jiaxing.json", "/locations/v1/cities/translate", q="嘉兴")[0]
    loc = loc_item["Key"]
    call("api_current_jiaxing.json", f"/currentconditions/v1/{loc}.json", details="true")
    call("api_daily5_jiaxing.json", f"/forecasts/v1/daily/5day/{loc}.json", details="true")
    call("api_hourly12_jiaxing.json", f"/forecasts/v1/hourly/12hour/{loc}.json", details="true")
    call("api_air_jiaxing.json", f"/airquality/v1/global/observations/{loc}.json")
    try:
        call("api_alerts_jiaxing.json", f"/alerts/v1/{loc}.json")
    except Exception as exc:
        print(f"[!] 预警样本抓取失败(无预警时也可能非 200): {exc}")
    try:
        geo = loc_item.get("GeoPosition") or {}
        call("api_nowcast_jiaxing.json", "/nowcast_cn/v3/basic.json",
             q=f"{geo['Latitude']},{geo['Longitude']}")
    except Exception as exc:
        print(f"[!] 短临样本抓取失败(非中国区域/配额限制时): {exc}")
    return 0


if __name__ == "__main__":
    code = main(sys.argv)
    if code == 0 and "--no-api" not in sys.argv:
        code = fetch_api_samples()
    sys.exit(code)
