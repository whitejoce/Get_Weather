import requests
import json

url = "https://j.i8tq.com/weather2020/search/city.js"
# with open("city.json", "w", encoding="utf-8") as f:
#     raw_content = requests.get(url).text
#     #去掉开头的var city_data = 
#     f.write(raw_content[15:])

with open("city.json", "r", encoding="utf-8") as f:
    raw_content = requests.get(url).text
    raw_data = json.loads(raw_content[15:])
    #找到"NAMECN"是"北京"的,递归查找
    def find_city_by_name(name, data):
        for k, v in data.items():
            if k == "NAMECN" and v == name:
                return data
            if isinstance(v, dict):
                result = find_city_by_name(name, v)
                if result:
                    return result
        return None
    city = find_city_by_name("北京", raw_data)
    print(city['AREAID'])