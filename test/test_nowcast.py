"""分钟级短临降水单元测试: 合成/强度条/文本渲染, 全部离线。

实测依据(2026-10): Intensity 浮点(小雨峰值 0.236, 疑为 mm/h); Interval 步长 6 分钟
(文档写 5); Description 三态官方原句(无雨/附近有雨/本地将下雨)。
"""

import datetime

import GetWeather
from GetWeather import AirQuality, WeatherReport, WeatherSnapshot

DT = datetime.datetime(2026, 10, 5, 9, 30)


def mc(intensity, pre_type="", now=DT, **extra):
    payload = {"Intensity": intensity, "PreType": pre_type, **extra}
    return GetWeather.synthesize_nowcast(payload, now=now)


def make_report(minute_cast=None) -> WeatherReport:
    return WeatherReport(
        summary="今天有小雨，比昨天凉爽一些，现在20°，空气不错。",
        snapshot=WeatherSnapshot(
            city_cn="瓯海",
            city_en="ouhai",
            description="阴",
            temp_now="20.7",
            humidity="88%",
            date="10月05日(星期一)",
            update_time="09:30",
            max_temp="25℃",
            min_temp="17℃",
        ),
        air_quality=AirQuality(aqi="17", level="优", pm25="17"),
        umbrella="不用带伞",
        alarms=[],
        minute_cast=minute_cast,
    )


# ---------------- synthesize_nowcast: 无雨/附近有雨 ----------------

def test_synthesize_no_rain():
    assert mc([0.0] * 24) == {
        "两小时内有雨": False,
        "摘要": "未来两小时无降水",
        "降水类型": "",
    }


def test_synthesize_no_rain_prefers_official_description():
    data = mc([0.0] * 20, Description="未来2小时无降水", Interval=6)
    assert data["摘要"] == "未来2小时无降水"
    assert data["官方描述"] == "未来2小时无降水"


def test_synthesize_nearby_rain_state():
    """本地点无雨但附近有回波(厦门实测形态): 官方建议带伞, 附近降雨带距离。"""
    data = mc([0.0] * 20, Description="附近有降水，出门建议带伞",
              IfPre=True, IsLocalPre=False, NearestPre=4, Interval=6)
    assert data["两小时内有雨"] is False
    assert data["摘要"] == "附近有降水，出门建议带伞"
    assert data["附近降雨"] == {"距离km": 4}
    assert "强度序列" not in data  # 无雨不输出序列


def test_synthesize_trace_below_epsilon_is_no_rain():
    # 低于阈值的毛毛雨/噪声不触发"有雨"
    assert mc([0.05] * 24)["两小时内有雨"] is False


# ---------------- synthesize_nowcast: 本地有雨 ----------------

def test_synthesize_rain_later_within_window():
    seq = [0.0] * 5 + [0.12, 0.2, 0.42, 0.2, 0.12] + [0.0] * 14
    data = mc(seq, pre_type="雨")
    assert data["两小时内有雨"] is True
    assert data["开始"] == "约25分钟后"
    assert data["开始钟点"] == "09:55"  # 09:30 + 25min
    assert data["持续分钟"] == 25
    assert data["渐止钟点"] == "10:20"  # 09:30 + 50min(末格结束)
    assert data["窗口末端仍有降雨"] is False
    assert data["峰值强度"] == 0.42
    assert data["摘要"] == "约25分钟后开始降雨，持续约25分钟"  # 泛化"雨"不标注
    assert data["强度序列"] == seq
    assert data["步长分钟"] == 5  # 缺省步长


def test_synthesize_official_description_overrides_fallback():
    seq = [0.0] * 3 + [0.2, 0.3, 0.2] + [0.0] * 3
    data = mc(seq, Description="20分钟后开始下小雨，下下停停",
              ShortPhrase="20分钟后开始下小雨")
    assert data["摘要"] == "20分钟后开始下小雨，下下停停"
    assert data["官方描述"] == "20分钟后开始下小雨，下下停停"
    assert data["官方短语"] == "20分钟后开始下小雨"
    # 钟点换算字段仍在(供雨具行使用): 第4格起雨 = 09:30 + 15min
    assert data["开始钟点"] == "09:45"


def test_synthesize_interval_six_minutes():
    """Interval=6(实测值): 20 格全有雨 = 120 分钟完整窗口。"""
    data = mc([0.3] * 20, Interval=6)
    assert data["步长分钟"] == 6
    assert data["持续分钟"] == 120
    assert data["窗口末端仍有降雨"] is True
    assert data["摘要"] == "当前正在降雨，120分钟内暂无停歇迹象"


def test_synthesize_rain_later_snow_type_annotated():
    seq = [0.0] * 5 + [0.12, 0.2, 0.42, 0.2, 0.12] + [0.0] * 14
    data = mc(seq, pre_type="雪")
    assert "（雪）" in data["摘要"]
    assert "开始降雪" in data["摘要"]


def test_synthesize_raining_now_stops_within_window():
    seq = [0.3, 0.5, 0.2] + [0.0] * 21
    data = mc(seq)
    assert data["开始"] == "当前"
    assert data["开始钟点"] == "已开始"
    assert data["持续分钟"] == 15
    assert data["渐止钟点"] == "09:45"
    assert data["窗口末端仍有降雨"] is False
    assert data["摘要"] == "当前正在降雨，约15分钟后渐止"


def test_synthesize_raining_now_truncated_no_stop_claim():
    """瓯海场景: 序列末端仍有降雨, 不得断言"渐止"。"""
    data = mc([0.3] * 20)
    assert data["窗口末端仍有降雨"] is True
    assert data["渐止钟点"] is None
    assert data["持续分钟"] == 100
    assert data["摘要"] == "当前正在降雨，100分钟内暂无停歇迹象"


def test_synthesize_rain_later_truncated():
    seq = [0.0] * 5 + [0.2] * 15  # 20 格, 末端仍有雨
    data = mc(seq)
    assert data["窗口末端仍有降雨"] is True
    assert data["开始钟点"] == "09:55"
    assert data["摘要"] == "约25分钟后开始降雨，之后持续有雨"


def test_synthesize_datetime_used_as_clock_anchor():
    """不注入 now 时, 钟点换算以数据自带 Datetime(带时区)为锚。"""
    seq = [0.0] * 5 + [0.2, 0.3, 0.2] + [0.0] * 16
    data = GetWeather.synthesize_nowcast(
        {"Intensity": seq, "PreType": "雨", "Datetime": "2026-10-05T09:30:00+08:00"}
    )
    assert data["开始钟点"] == "09:55"
    assert data["渐止钟点"] == "10:10"


# ---------------- nowcast_peak_text ----------------

def test_peak_text_thresholds():
    f = GetWeather.nowcast_peak_text
    assert f(0.236) == "较弱"  # 实测小雨样本
    assert f(0.49) == "较弱"
    assert f(0.5) == "中等"
    assert f(1.9) == "中等"
    assert f(2.0) == "较强"
    assert f(7.9) == "较强"
    assert f(8.0) == "很强"
    assert f(None) == ""


# ---------------- minute_cast_sparkline ----------------

def test_sparkline_normalizes_to_peak():
    bar = GetWeather.minute_cast_sparkline([0.0, 0.1, 0.2, 0.4, 0.0])
    assert len(bar) == 5
    assert bar[0] == "▁"
    assert bar[3] == "▇"  # 峰值映射到最高块


def test_sparkline_empty_or_dry():
    assert GetWeather.minute_cast_sparkline([]) == ""
    assert GetWeather.minute_cast_sparkline([0.0] * 24) == ""
    assert GetWeather.minute_cast_sparkline([0.05] * 24) == ""  # 低于阈值视为无降水


# ---------------- 文本渲染 ----------------

def test_render_layout_order_and_temp_range():
    """生活建议顺序: 概况 -> 雨具 -> 短临; 温度范围低~高。"""
    seq = [0.0] * 5 + [0.12, 0.3, 0.42, 0.3, 0.12] + [0.0] * 14
    text = make_report(minute_cast=mc(seq)).as_text(color_mode="none")
    assert text.index("📝 天气概况") < text.index("☂️ 雨具携带") < text.index("⏱️ 短临降水")
    assert "17℃ ~ 25℃" in text


def test_render_no_rain_compact():
    text = make_report(minute_cast=mc([0.0] * 24)).as_text(color_mode="none")
    assert "未来两小时无降水" in text
    assert "短临降水" not in text  # 无雨不展开区块
    assert "不用带伞" not in text  # 短临可用时替代 dataZS 静态指数


def test_render_nearby_rain_umbrella_without_block():
    """附近有雨: 雨具行给距离提示, 不展开短临区块(本地点无序列可画)。"""
    data = mc([0.0] * 20, Description="附近有降水，出门建议带伞",
              NearestPre=4, Interval=6)
    text = make_report(minute_cast=data).as_text(color_mode="none")
    assert "附近4km有降雨，出门建议带伞" in text
    assert "⏱️" not in text


def test_render_rain_later_uses_clock():
    seq = [0.0] * 5 + [0.12, 0.3, 0.42, 0.3, 0.12] + [0.0] * 14
    text = make_report(minute_cast=mc(seq)).as_text(color_mode="none")
    assert "09:55 前后有雨，建议带伞" in text
    assert "约 09:55 开始降雨，持续约25分钟，雨势较弱" in text
    assert "短临降水(未来2小时)" in text
    assert "▇" in text  # 强度条已渲染
    assert "+2h" in text


def test_render_official_description_preferred():
    """官方描述存在时, 短临行直接用官方原句, 不追加雨势措辞。"""
    seq = [0.0] * 3 + [0.2, 0.3, 0.2] + [0.0] * 3  # 9 格 x 5min = 45 分钟窗口
    data = mc(seq, Description="20分钟后开始下小雨，下下停停",
              ShortPhrase="20分钟后开始下小雨")
    text = make_report(minute_cast=data).as_text(color_mode="none")
    assert "⏱️ 短临降水(未来45分钟)：20分钟后开始下小雨，下下停停" in text
    assert "雨势" not in text


def test_render_raining_now_truncated_ouhai_case():
    """瓯海场景(缺省步长5): 不断言渐止, 窗口按实际时长标注。"""
    seq = [0.32, 0.40, 0.45, 0.50, 0.48] * 4  # 20 格持续有雨
    text = make_report(minute_cast=mc(seq)).as_text(color_mode="none")
    assert "正在下雨，建议带伞" in text
    assert "100分钟内持续降雨，暂无停歇迹象" in text
    assert "渐止" not in text
    assert "短临降水(未来100分钟)" in text
    assert "+100min" in text


def test_render_interval_six_full_window():
    """Interval=6: 20 格 = 120 分钟完整窗口, 标注回到 未来2小时/+2h。"""
    seq = [0.32, 0.40, 0.45, 0.50, 0.48] * 4
    text = make_report(minute_cast=mc(seq, Interval=6)).as_text(color_mode="none")
    assert "短临降水(未来2小时)" in text
    assert "120分钟内持续降雨" in text
    assert "+2h" in text


def test_render_raining_now_stops_with_clock():
    text = make_report(minute_cast=mc([0.3, 0.5, 0.2] + [0.0] * 21)).as_text(color_mode="none")
    assert "持续到约 09:45 前后渐止" in text


def test_render_ansi_colors_bar():
    seq = [0.0] * 5 + [0.12, 0.3, 0.12] + [0.0] * 16
    text = make_report(minute_cast=mc(seq)).as_text(color_mode="ansi")
    assert "\033[94m" in text  # 强度条用冷色(蓝)渲染


def test_render_without_nowcast_keeps_umbrella():
    text = make_report().as_text(color_mode="none")
    assert "不用带伞" in text
    assert "短临降水" not in text
