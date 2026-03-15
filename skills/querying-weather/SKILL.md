---
name: querying-weather
description: 查询指定城市或当前位置的实时天气信息。当用户询问天气、气温或提到需要天气数据时使用。
---

# Querying Weather Skill

## 目标
使用 `scripts/GetWeather.py` 脚本来查询实时天气信息。

## 执行步骤
1. **确定目标城市**：
   - 提取用户指定的城市名称。如果不指定，则自动进行定位。

2. **调用查询脚本**：
   - 使用终端工具执行 `python scripts/GetWeather.py --city <城市名>` 查询特定城市。
   - 如果没有城市名，执行 `python scripts/GetWeather.py` 自动定位。

3. **解析与返回**：
   - 将脚本在终端输出的天气信息结果或错误提示返回给用户。
