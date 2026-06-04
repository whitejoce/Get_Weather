# API Documentation

本文档说明本仓库对外可用的 Python 接口、CLI 参数，以及当前依赖的上游数据结构。

## Python 接口

推荐使用 `get_weather.WeatherClient`：

```python
from get_weather import WeatherClient

client = WeatherClient(timeout=10, retries=1)
city_code = client.get_city_code("北京")
weather_text = client.get_weather(city_code)
print(weather_text)
```

兼容旧脚本的函数仍可从 `GetWeather.py` 或 `get_weather` 导入：

- `get_CityName() -> tuple[str, str]`：自动定位城市，返回城市名和城市代码。
- `get_city_code(city: str) -> str`：通过中文城市名查询城市代码。
- `get_weather(city_code: str, dump_response_path: str | None = None) -> str`：通过城市代码查询并格式化天气文本。
- `weather_alarm(source: str) -> Iterable[str]`：解析预警数据并返回输出行。
- `debug_mode(city_code: str, output_file="debug_results.json") -> list[dict]`：检查上游 URL 状态码。

库函数不再直接调用 `sys.exit()`；失败时会抛出 `WeatherError` 及其子类：

- `InvalidCityNameError`
- `CityNotFoundError`
- `NetworkError`
- `ParseError`

## CLI 参数

```bash
python GetWeather.py [--city 城市名] [--output 0|1] [--debug] [--dump-response]
```

- `--city`：指定中文城市名，例如 `北京`。不指定时尝试自动定位。
- `--output`：`0` 为终端输出，`1` 为 Tkinter 窗口输出。
- `--debug`：只检查上游 URL 状态码。
- `--dump-response`：保存 `weather_index` 原始响应到 `response.html`，默认不保存。
- `--debug-output`：Debug 模式结果文件，默认 `debug_results.json`；传入空字符串可禁用写入。

## 上游接口

当前脚本依赖以下上游页面或接口：

- 城市定位：`http://wgeo.weather.com.cn/ip/?_={timestamp}`
- 城市列表：`https://j.i8tq.com/weather2020/search/city.js`
- 天气索引：`http://d1.weather.com.cn/weather_index/{city_code}.html?_={timestamp}`
- 温度区间：`http://d1.weather.com.cn/dingzhi/{city_code}.html?_={timestamp}`
- 天气摘要：`https://www.qweather.com/weather/{city_en}-{city_code}.html`

这些都不是本项目维护的稳定 API。上游结构变化时，本项目解析逻辑可能需要同步更新。

## `dataSK`

`weather_index` 页面中的实时天气数据，示例：

```json
{
  "nameen": "beijing",
  "cityname": "北京",
  "city": "101010100",
  "temp": "32",
  "WD": "北风",
  "WS": "1 级",
  "SD": "13%",
  "time": "09:40",
  "aqi": "35",
  "aqi_pm25": "35",
  "weather": "晴",
  "limitnumber": "不限行",
  "date": "06月19日(星期六)"
}
```

## `alarmDZ`

无预警：

```json
{"w": []}
```

有预警：

```json
{
  "w": [
    {
      "w5": "高温",
      "w7": "蓝色",
      "w8": "2021-06-18 15:41",
      "w9": "市气象台发布高温蓝色预警信号：预计日最高气温将在35℃以上。",
      "w11": "10101-20210618154146-0701.html",
      "w13": "北京市发布高温蓝色预警"
    }
  ]
}
```

## `dataZS`

生活指数数据，脚本当前主要使用 `ys_des_s` 作为雨具建议：

```json
{
  "zs": {
    "date": "2021061918",
    "ys_name": "雨伞指数",
    "ys_hint": "不带伞",
    "ys_des_s": "天气较好，不用带雨伞。"
  },
  "cn": "北京"
}
```

``` json
{
   "zs":{
      "date":"2021061918",
      "lk_name":"路况指数",
      "lk_hint":"干燥",
      "lk_des_s":"天气较好，路面较干燥，路况较好。",
      "cl_name":"晨练指数",
      "cl_hint":"较适宜",
      "cl_des_s":"请选择避风的地点晨练，避免迎风锻炼。",
      "gj_name":"逛街指数",
      "gj_hint":"适宜",
      "gj_des_s":"这种好天气去逛街可使身心畅快放松。",
      "pl_name":"空气污染扩散条件指数",
      "pl_hint":"中",
      "pl_des_s":"易感人群应适当减少室外活动。",
      "co_name":"舒适度指数",
      "co_hint":"舒适",
      "co_des_s":"白天温度宜人，风力不大。",
      "pj_name":"啤酒指数",
      "pj_hint":"适宜",
      "pj_des_s":"天气炎热，可适量饮用啤酒，不要过量。",
      "hc_name":"划船指数",
      "hc_hint":"适宜",
      "hc_des_s":"天气较好，适宜划船及嬉玩水上运动。",
      "gl_name":"太阳镜指数",
      "gl_hint":"很必要",
      "gl_des_s":"建议佩戴透射比2级且UV400的遮阳镜",
      "uv_name":"紫外线强度指数",
      "uv_hint":"很强",
      "uv_des_s":"涂擦SPF20以上，PA++护肤品，避强光。",
      "wc_name":"风寒指数",
      "wc_hint":"无",
      "wc_des_s":"温度未达到风寒所需的低温，稍作防寒准备即可。",
      "ct_name":"穿衣指数",
      "ct_hint":"热",
      "ct_des_s":"适合穿T恤、短薄外套等夏季服装。",
      "pk_name":"放风筝指数",
      "pk_hint":"较适宜",
      "pk_des_s":"气温略高，放风筝时戴上太阳帽。",
      "ac_name":"空调开启指数",
      "ac_hint":"较少开启",
      "ac_des_s":"体感舒适，不需要开启空调。",
      "dy_name":"钓鱼指数",
      "dy_hint":"较适宜",
      "dy_des_s":"风稍大会对垂钓产生一定影响。",
      "ls_name":"晾晒指数",
      "ls_hint":"极适宜",
      "ls_des_s":"天气不错，抓紧时机让衣物晒太阳吧。",
      "gm_name":"感冒指数",
      "gm_hint":"少发",
      "gm_des_s":"感冒机率较低，避免长期处于空调屋中。",
      "xc_name":"洗车指数",
      "xc_hint":"适宜",
      "xc_des_s":"天气较好，适合擦洗汽车。",
      "tr_name":"旅游指数",
      "tr_hint":"适宜",
      "tr_des_s":"天气较好，可尽情地享受大自然的风光。",
      "nl_name":"夜生活指数",
      "nl_hint":"较适宜",
      "nl_des_s":"只要您稍作准备就可以放心外出。",
      "xq_name":"心情指数",
      "xq_hint":"好",
      "xq_des_s":"好天气会带来一天的好心情。",
      "yh_name":"约会指数",
      "yh_hint":"较适宜",
      "yh_des_s":"不用担心天气来调皮捣乱而影响了兴致。",
      "yd_name":"运动指数",
      "yd_hint":"适宜",
      "yd_des_s":"天气较好，尽情感受运动的快乐吧。",
      "ag_name":"过敏指数",
      "ag_hint":"不易发",
      "ag_des_s":"除特殊体质，无需担心过敏问题。",
      "mf_name":"美发指数",
      "mf_hint":"一般",
      "mf_des_s":"注意清洁，建议选用防晒滋润型护发品。",
      "ys_name":"雨伞指数",
      "ys_hint":"不带伞",
      "ys_des_s":"天气较好，不用带雨伞。",
      "fs_name":"防晒指数",
      "fs_hint":"极强",
      "fs_des_s":"需涂擦SPF大于20，PA++，护肤品。",
      "pp_name":"化妆指数",
      "pp_hint":"去油防晒",
      "pp_des_s":"请选用水质无油粉底霜。",
      "zs_name":"中暑指数",
      "zs_hint":"无中暑风险",
      "zs_des_s":"天气舒适，对易中暑人群来说非常友善。",
      "jt_name":"交通指数",
      "jt_hint":"良好",
      "jt_des_s":"气象条件良好，车辆可以正常行驶。",
      "gz_name":"干燥指数",
      "gz_hint":"非常干燥",
      "gz_des_s":"空气干燥，极易引起皮肤水分流失，建议涂抹防晒霜，多喝水保持身体滋润。"
   }
  "cn": "北京"
}
```
