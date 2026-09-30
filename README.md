# Get_Weather

天气查询工具：单文件 CLI + AI Skill + 官方 API 数据源（可选）。基于中国天气网公开数据与华风爱科开放平台。

```text
今天白天有小雨，夜晚多云，温度和昨天差不多，现在24°，有风，空气不错。
```

## 快速开始（CLI）

```bash
pip install -r requirements.txt

python GetWeather.py                                  # 自动 IP 定位
python GetWeather.py --city-name 北京                  # 指定城市
python GetWeather.py --city-code 101010100            # 指定城市代码
python GetWeather.py --city-name 北京 --color-mode rich  # 终端配色: none/ansi/rich
python GetWeather.py --city-name 北京 --output 1       # Tkinter 窗口输出
python GetWeather.py --debug                          # 检查上游接口状态码
```

- 数据源：中国天气网（定位 wgeo / 城市搜索 toy1 / 实况预报 d1），每次查询 2~3 个轻量请求（~20KB）
- 一句话摘要由本地合成（句式对齐和风天气，规律见 [test/README.md](./test/README.md)），无第三方页面依赖

## AI Skill

`skills/querying-weather/`（可安装于 `~/.pi/agent/skills/` 等位置）：

```bash
python scripts/GetWeather.py --city-name 嘉兴 --json   # 清洗版结构化 JSON（推荐给 AI）
python scripts/GetWeather.py --city-name 嘉兴 --raw    # 原始接口 JSON（dataSK/dataZS/alarmDZ/fc/fc40）
python scripts/GetWeather.py --city-name 嘉兴          # 人类可读文本
```

- 进度信息走 stderr，stdout 纯 JSON 可直接解析
- **官方 API 数据源（可选）**：存在 API Key 时自动改走[华风爱科开放平台](https://platform.weathercn.com)（中国气象局华风 × AccuWeather），额外提供官方原生摘要（含"比昨天"）、日出日落/月相、逐小时预报、MEP 空气质量、结构化预警；无 Key 或调用失败自动回退网页方案
- Key 配置：环境变量 `WEATHERCN_API_KEY` / `API_KEY`，或脚本目录 / 当前目录 `.env`（参考 `.env.example`）

## 测试

```bash
pip install -r requirements-dev.txt
python -m pytest test/ -q        # 45+ 个离线测试，不发网络请求
python test/fetch_fixtures.py    # 刷新本地样本(需 .env 中的 API_KEY 时含官方 API)
```

## 文档

- [test/README.md](./test/README.md) — 上游接口链接梳理 / 样本说明 / 摘要句式分析（活文档）
- [docs/API.md](./docs/API.md) — 天气网接口字段说明
- [skills/querying-weather/SKILL.md](./skills/querying-weather/SKILL.md) — Skill 用法与 AI 解读要点

## 数据来源与声明

- 城市定位：中国天气网 `wgeo.weather.com.cn`
- 天气数据：中国天气网 `d1.weather.com.cn`（公开网页数据解析）
- 可选官方 API：华风爱科开放平台 `openapi.weathercn.com`

> 本项目解析公开网页数据，上游页面结构可能变化导致解析失败；请遵守数据来源网站使用规则，避免高频请求。

## License

[MIT License](./LICENSE)
