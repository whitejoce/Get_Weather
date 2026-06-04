# Get_Weather
<div align="center">

[![Python](https://img.shields.io/badge/Python-3.10%2B-green.svg)](https://www.python.org/) [![License](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)

</div>

> 使用`Codex GPT-5.5 xhigh`优化代码仓库

Get_Weather 是一个基于中国天气网和和风天气公开网页数据的 Python 天气查询工具。项目支持自动定位城市、指定城市查询、实时天气输出、气象预警展示，并提供 Skill 集成。

## 功能特性

- 支持自动定位到市级城市，也支持通过 `--city` 指定城市。
- 输出实时天气、体感温度、温度区间、湿度、空气质量、雨具建议、更新时间和气象预警。
- 提供 Debug 模式，用于检查上游数据地址的访问状态。
- 保留 `python GetWeather.py` 兼容入口，并提供可测试的 `get_weather` Python 包。
- 内置 Skill：`skills/querying-weather`。

## 安装

安装运行依赖：

```bash
python -m pip install -r requirements.txt
```

安装开发和测试依赖：

```bash
python -m pip install -r requirements-dev.txt
```

## 命令行使用

| 命令 | 说明 |
| --- | --- |
| `python GetWeather.py` | 自动定位城市并查询天气。 |
| `python GetWeather.py --city 北京` | 查询指定城市天气。 |
| `python GetWeather.py --city 北京 --output 1` | 使用 Tkinter 窗口显示结果。 |
| `python GetWeather.py --debug --city 北京` | 检查指定城市相关上游地址的状态码。 |
| `python GetWeather.py --city 北京 --dump-response` | 保存 `weather_index` 原始响应到 `response.html`，用于调试解析问题。 |

## Python API

```python
from get_weather import WeatherClient

client = WeatherClient(timeout=10, retries=1)
city_code = client.get_city_code("北京")
weather_text = client.get_weather(city_code)
print(weather_text)
```

历史函数仍可从 `GetWeather.py` 或 `get_weather` 导入。新代码建议优先使用 `get_weather.WeatherClient`。

## Skill

仓库包含一个 Skill：`skills/querying-weather`。

Skill 元数据位于：`skills/querying-weather/SKILL.md`

Skill 执行脚本位于：`skills/querying-weather/scripts/GetWeather.py`

## 示例输出

```text
 今天白天晴，夜晚晴，温度和昨天差不多，现在35°，有风，空气不错。

 ===================================
 定位城市:  北京
 实时天气:  晴
 体感温度:  35℃
 温度区间:  36℃ ~ 21℃
 空气湿度:  15%
 空气质量:  31(优),PM2.5: 31
 雨具携带:  天气较好，不用带雨伞。
 [更新时间: 06月20日(星期日) 12:50]
 ===================================
```

## 开发

运行测试：

```bash
python -m pytest
```

测试使用模拟的上游响应，不依赖实时天气数据。GitHub Actions 会在 Python 3.10、3.11、3.12、3.13 上运行测试。

## 数据来源和限制

- 城市定位：中国天气网 `http://wgeo.weather.com.cn/ip/`
- 天气数据：中国天气网 `http://www.weather.com.cn/`
- 天气摘要：和风天气 `https://www.qweather.com/`

> 本项目解析公开网页数据。上游页面结构、访问策略和字段内容可能变化，相关变化可能导致解析失败。**请遵守数据来源网站的使用规则，并避免高频请求。**

上游接口和字段说明见 [API.md](./API.md)。

## License

Get_Weather 基于 [MIT License](./LICENSE) 发布。
