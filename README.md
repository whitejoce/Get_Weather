# Get_Weather

中文天气信息获取脚本 - 自动定位并获取当地天气信息

[![Python 3.x](https://img.shields.io/badge/Python-3.x-green.svg)](https://docs.python.org/3/download.html)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/whitejoce/Get_Weather/blob/main/LICENSE)

## 关于

本代码仓库采用MIT许可协议（[The MIT License](https://github.com/whitejoce/Get_Weather/blob/main/LICENSE)）

我的Code代码仓库整合了此脚本,添加了查询城市天气(生活助手):[LifeHelper.py](https://github.com/whitejoce/Code/blob/main/Code/LifeHelper.py)

> 基于本项目的[安卓APP Demo](https://github.com/whitejoce/Code/tree/main/Android/NewWeather) ， [DeepWiki for this Repository](https://deepwiki.com/whitejoce/Get_Weather)

* * *

## 特性

- ✨ 自动IP定位（仅限国内）
- 🌤️ 实时天气信息
- 🌡️ 温度、湿度、空气质量
- ⚠️ 气象预警通知
- 🎯 支持手动指定城市
- 💻 命令行和GUI两种输出模式
- 🔍 Debug模式检查接口状态

* * *

## 安装

### 1. 克隆仓库

```bash
git clone https://github.com/whitejoce/Get_Weather.git
cd Get_Weather
```

### 2. 安装依赖

使用 pip 安装所需库：

```bash
pip install -r requirements.txt
```

或手动安装：

```bash
pip install requests beautifulsoup4
```

* * *

## 使用方法

### 基本使用（自动定位）

```bash
python GetWeather.py
```

脚本会自动根据您的IP地址定位到市级，并显示当地天气信息。

### 指定输出模式

```bash
# 命令行输出（默认）
python GetWeather.py --output 0

# GUI窗口输出
python GetWeather.py --output 1
```

### Debug 模式

检查各个API接口的状态：

```bash
python GetWeather.py --debug --city 101280601
```

### 查看帮助

```bash
python GetWeather.py --help
```

* * *

## 实现方法

> 通过获取定位（定位到市级），爬取当地的天气。
> 
> 脚本中采用的接口不同于网上（网上的接口天气不更新了），应该是"全网首发"     ; )
>
> 定位接口（仅限国内）: [中国天气网](http://wgeo.weather.com.cn/ip/)
>
> 天气数据来源网站: [中国天气网](http://www.weather.com.cn/),[和风天气](https://www.qweather.com/)

* * *

## 代码效果

```
今天白天晴，夜晚晴，温度和昨天差不多，现在35°，有风，空气不错。

===================================
定位城市:  北京
实时天气:  晴
体感温度:  35℃
温度区间:  21℃ ~ 36℃
空气湿度:  15%
空气质量:  31(优),PM2.5: 31
雨具携带:  天气较好，不用带雨伞。
[更新时间: 06月20日(星期日) 12:50]
===================================
[!]气象部门发布1则预警,请注意:
[1]市气象台2021年6月18日15时45分发布高温蓝色预警信号:
预计，19日至20日，本市大部分地区日最高气温将在35℃以上，请注意防范。
（预警信息来源：国家预警信息发布中心）
```

* * *

## 接口信息

提供接口的相关信息，供大家自定义天气窗口

接口: `http://d1.weather.com.cn/weather_index/[城市ID].html?_=[时间戳(毫秒)]`

详细API说明: [API.md](./API.md)

* * *

## 系统要求

- Python 3.6+
- requests >= 2.25.0
- beautifulsoup4 >= 4.9.0

* * *

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

[MIT License](LICENSE)
