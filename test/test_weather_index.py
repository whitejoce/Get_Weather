"""天气数据接口本地样本解析测试(全部离线, 不发网络请求)。

样本见 test/README.md 的链接梳理表。
"""

import re
from pathlib import Path

import GetWeather

FIXTURES = Path(__file__).resolve().parent / "sample"
JIAXING = "101210301"


def load(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


# ---------- 接口 3: weather_index (dataSK/dataZS/alarmDZ/cityDZ/fc) ----------


def test_weather_index_dataSK_realtime():
    data_sk = GetWeather.extract_json_block(load("weather_index_jiaxing.html"), "dataSK")

    assert data_sk["cityname"] == "嘉兴"
    assert data_sk["nameen"] == "jiaxing"
    assert data_sk["city"] == JIAXING
    assert data_sk["SD"].endswith("%")
    assert data_sk["aqi"].isdigit()
    assert data_sk["aqi_pm25"].isdigit()
    assert data_sk["date"] and data_sk["time"]


def test_weather_index_cityDZ_forecast_today():
    info = GetWeather.extract_json_block(load("weather_index_jiaxing.html"), "cityDZ")[
        "weatherinfo"
    ]

    assert "temp" in info
    assert "tempn" in info
    assert info["weather"]


def test_weather_index_dataZS_life_indices():
    zs = GetWeather.extract_json_block(load("weather_index_jiaxing.html"), "dataZS")["zs"]

    assert zs["ys_name"] == "雨伞指数"
    assert zs["ys_hint"]
    assert zs["ys_des_s"]


def test_weather_index_fc_five_days():
    fc = GetWeather.extract_json_block(load("weather_index_jiaxing.html"), "fc")["f"]

    assert len(fc) >= 5
    assert fc[0]["fj"] == "今天"
    assert fc[0]["fc"] and fc[0]["fd"]  # 最高/最低温


# ---------- 接口 4: dingzhi (参考对照) ----------


def test_fc0_today_matches_dingzhi_reference():
    """对照: fc[0] 与 dingzhi 接口数据等价, 故日常查询不请求 dingzhi。"""
    fc0 = GetWeather.extract_json_block(load("weather_index_jiaxing.html"), "fc")["f"][0]
    ref = GetWeather.extract_json_block(
        load("dingzhi_jiaxing.html"), f"cityDZ{JIAXING}"
    )["weatherinfo"]

    assert f"{fc0['fc']}℃" == ref["temp"]
    assert f"{fc0['fd']}℃" == ref["tempn"]


# ---------- 接口 5: qweather (摘要 + AQI 等级) ----------


def test_qweather_summary_and_aqi_level():
    summary, aqi_level = GetWeather.parse_qweather_summary(load("qweather_jiaxing.html"))

    assert summary  # 非空摘要, 如 "今天白天有小雨..."
    assert aqi_level  # 如 "优"


# ---------- 接口 1: wgeo (IP 自动定位) ----------


def test_wgeo_ip_response_shape():
    """定位接口样本字段与 get_CityName 的正则逻辑一致。"""
    text = load("wgeo_ip.txt")

    addr = re.findall('addr="(.*?)"', text)
    city_id = re.findall('id="(.*?)"', text)

    assert addr and city_id
    assert addr[0].split(",")[-1]  # 省,市,区 的最后一段
    assert city_id[0].isdigit()


# ---------- get_weather 离线全流程 ----------


def test_get_weather_offline_local_summary(monkeypatch):
    """get_weather 共 2 个请求(weather_index+calendar_new), 摘要与 AQI 等级本地合成。"""
    idx = load("weather_index_jiaxing.html")
    cal = load("calendar_new_jiaxing.html")
    requested = []

    def fake_fetch_text(url, headers=None, *, timeout=10):
        requested.append(url)
        if "weather_index" in url:
            return idx
        if "calendar_new" in url:
            return cal
        raise AssertionError(f"不应请求: {url}")

    monkeypatch.setattr(GetWeather, "fetch_text", fake_fetch_text)

    report = GetWeather.get_weather(JIAXING)

    assert report.snapshot.city_cn == "嘉兴"
    assert report.snapshot.max_temp == "26℃"  # fc[0].fc
    assert report.snapshot.min_temp == "22℃"  # fc[0].fd
    assert report.air_quality.level == "优"  # 本地分级(原为和风页面字段)
    assert report.summary.startswith("今天白天")  # 本地合成摘要
    assert "空气不错" in report.summary
    assert len(requested) == 2  # 仅 weather_index + calendar_new
    assert not any("qweather" in u or "dingzhi" in u for u in requested)
