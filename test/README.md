# test/ — 请求链接梳理与本地读取测试

本目录保存各上游接口的**真实响应样本**（`sample/`），pytest 测试全部离线运行（不发网络请求），用于验证解析逻辑（`extract_json_block` / `build_alarm_messages` / `parse_qweather_summary` / `get_city_code` / `main_weather_process` 参数路由）与上游数据格式保持一致。

## 目录结构

```
test/
├── sample/        # 本地样本: 各上游接口的真实响应(离线测试数据源)
├── conftest.py    # 注入仓库根路径, 使测试可 import GetWeather
├── fetch_fixtures.py  # 一键抓取/刷新 sample/ 下的样本
├── test_alarm.py          # 预警提取与格式化
├── test_city.py           # 城市码查找: toy1 轻量搜索 + city.js 回退
├── test_weather_index.py  # 接口响应解析 + get_weather 离线全流程
├── test_main_process.py   # --city-name / --city-code 参数路由回归
├── test_summary.py        # 摘要本地合成单元测试(阅值/天气码表/昨日实测)
├── test_skill_json.py     # skill 脚本 --json/--raw 数据契约
└── test_api_provider.py   # 官方 API provider(定位/清洗映射/回退/密钥优先级)
```

## 运行

```bash
python -m pytest test/
```

## 请求链接梳理

所有请求均由 `GetWeather.py` 发起（`_=` 为毫秒时间戳，防缓存）。

| # | 用途 | URL | 必要请求头 | 本地样本 | 关键字段 |
|---|------|-----|-----------|----------|----------|
| 1 | IP 自动定位（省市区 → 城市代码） | `http://wgeo.weather.com.cn/ip/?_={ts}` | Cookie `f_city=杭州\|621005320\|`（URL 编码）+ Referer `http://www.weather.com.cn` | `sample/wgeo_ip.txt` | `addr="浙江,温州,乐清"` / `id="101210707"` |
| 2 | 城市名 → 城市代码 | `http://toy1.weather.com.cn/search?cityname={名}` | Referer | `sample/toy1_search_jiaxing.txt` | `"ref":"{代码}~{省拼音}~{城市名}~..."`，~ 分隔第 3 段需精确匹配（过滤模糊命中） |
| 2' | 城市名 → 城市代码（**回退**，仅搜索失败/未命中时） | `https://j.i8tq.com/weather2020/search/city.js` | UA | `sample/city.js`（`sample/city.json` 为去掉 `var city_data = ` 前缀的历史副本） | 递归查找 `NAMECN` → `AREAID` |
| 3 | 实时天气 + 生活指数 + 预警 + 5 日预报 | `http://d1.weather.com.cn/weather_index/{城市代码}.html?_={ts}` | Referer `http://www.weather.com.cn`（**缺失会 403**） | `sample/weather_index_jiaxing.html` | JS 变量 `cityDZ` / `alarmDZ` / `dataSK` / `dataZS` / `fc`；**温度区间取 `fc[0].fc/fd`** |
| 4 | 当日温度区间 | `http://d1.weather.com.cn/dingzhi/{城市代码}.html?_={ts}` | 同上 | `sample/dingzhi_jiaxing.html`（保留作等价性对照） | `cityDZ{代码}.weatherinfo.temp` / `tempn` |
| 5 | 天气摘要 + AQI 等级 | `https://www.qweather.com/weather/{城市英文名}-{城市代码}.html` | UA | `sample/qweather_jiaxing.html` | `div.current-abstract` / `p.city-air-chart__txt` |
| 6 | 预警详情页 | `https://www.weather.com.cn/alarm/newalarmcontent.shtml?file={w11}` | - | 未保存（链接由接口 3 的 `alarmDZ[].w11` 拼出） | - |
| 7 | 40 天日历预报 | `http://d1.weather.com.cn/calendar_new/{年}/{代码}_{年月}.html?_={ts}` | Referer | `sample/calendar_new_jiaxing.html` | `var fc40 = [...]`：35 天；**近 5 天 `cla:"obs"` 含 `maxobs/minobs` 实测高低温（昨日数据可取）**；`cla:"history"` 为历史均值 `hmax/hmin`；另有 `date/c1/c2(天气码)/max/min(今日预报)/hgl/hol(节假日)/blue/insuit/alins+als(黄历宜忌)` |
| 8 | 雷达图 | `https://d1.weather.com.cn/radar/JC_RADAR_{雷达站号}_JB_V3.html`（部分站为 `_JB.html`） | - | 未保存（JSONP `readerinfo`，站号表在 `j.i8tq.com/radar/radar2024.js`） | 图片序列 |

字段结构详见 [docs/API.md](../docs/API.md)。

另有轻量实时接口 `http://d1.weather.com.cn/sk_2d/{代码}.html`（200，约350B，独立 dataSK），`weather_index` 已含同款数据，未使用。

### 网页内嵌数据（无独立接口，需抓 shtml 页解析）

官网页面数据以内联 JS 变量服务端渲染（非 XHR）：

| 页面 | 大小 | 内嵌数据 |
|------|------|----------|
| `weather1d/{码}.shtml`（今日）/ `weather/{码}.shtml`（7天） | 66-75KB | `hour3data`（逐 3 小时预报）、`observe24h_data`（**昨日 13 时 → 今日 13 时**逐时实况：`od21`小时/`od22`温度/`od23`湿度/`od24`风向/`od25`风力） |
| `weather15dn/{码}.shtml`（乡镇 15 天） | 131KB | `eventDay/eventNight`（8 天温度）、`fifDay/fifNight`（15 天）、`sunup/sunset`（日出日落）、`villages`（乡镇级代码，如 `101210707005`） |
| `weather15d/{码}.shtml`（8-15 天）/ `weather40d/{码}.shtml`（40 天） | 59-119KB | HTML 表格（服务端渲染） |

注意：乡镇扩展码（`{码}005` 形式）在 d1 接口上不可用（返回伪 200 的 404 页）；`weather1h`（24 小时）页只是跳转壳。

### 和风摘要句式

`div.current-abstract` 的文本为服务端模板生成，30/30 样本均符合：

```
今天[白天{A}，夜晚{B}|{C}]，{温度比较}，现在{T}°[，{风}]，空气{空气}。
```

| 槽位 | 取值现律（实测） |
|------|------------------|
| 天气 A/B/C | 降水类带"有"前缀（有小雨/有阵雨/有中雨），晴/多云/阴不带；白天夜晚天气相同时多数仍拆分，仅降水类偶见合并为"今天X" |
| 温度比较 | `温度和昨天差不多` / `比昨天{热\|暖和\|凉爽}{一些\|很多}`（需昨日数据：可从 `calendar_new` 近 5 天 `maxobs/minobs` 实测值取，见接口 7） |
| 现在 T° | 和风自有实测温度，与 d1 `dataSK.temp` 差 -1.3~+2.2°（均值 -0.2°） |
| 风 | 无 / `有风`（多对应 d1 风力 2~3 级）/ `风很大`（多对应 ≥4 级）；按 d1 风力阈值重建可命中 24/30 |
| 空气 | `不错`↔AQI≤50（优），`一般`↔AQI 51-100（良），分界线 50 干净命中 30/30 |

摘要由本地合成，数据全部来自 `weather_index` 与 `calendar_new`：天气取 `cityDZ.weather`（回退 `fc[0].fa/fb` 天气码表），"比昨天"取昨日实测 vs 今日预报，阈值：`|Δ最高|≤1` 差不多、`2~4` 一些、`≥5` 很多，热/暖和分界约在最高温 24~25°。

## sample/ 样本说明

| 文件 | 内容 |
|------|------|
| `wgeo_ip.txt` | 接口 1 响应（定位到 浙江温州乐清） |
| `toy1_search_jiaxing.txt` | 接口 2 响应（搜索"嘉兴"，含模糊命中需过滤） |
| `city.js` | 接口 2' 原始响应（约 345KB，仅回退时使用） |
| `city.json` | 接口 2' 去前缀 JSON（历史副本，386KB） |
| `weather_index_jiaxing.html` | 接口 3 响应（嘉兴 101210301，含全部 5 个 JS 变量） |
| `dingzhi_jiaxing.html` | 接口 4 响应（备用参考，与 `fc[0]` 数据等价） |
| `calendar_new_jiaxing.html` | 接口 7 响应（fc40 40 天日历预报） |
| `qweather_jiaxing.html` | 接口 5 响应（和风天气嘉兴页） |
| `alarm1.json` | 北京 2 则预警样本（alarmDZ，2025-02） |
| `alarm2.json` | 无预警样本（`{"w":[]}`） |
| `qweather_summaries_30cities.json` | 和风摘要采集样本（句式参考） |

## 更新样本

```bash
python test/fetch_fixtures.py             # 抓取全部样本
python test/fetch_fixtures.py city.js     # 只抓取指定样本
```

> 请勿高频抓取，遵守数据源网站使用规则。
