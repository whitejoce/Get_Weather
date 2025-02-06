#!/usr/bin/python
# _*_coding: utf-8 _*_
# Coder:Whitejoce

import json
import re
import sys
import time

import bs4
import requests
import argparse

def create_headers(cookie=None, referer=None):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0'
    }
    if cookie:
        headers['Cookie'] = cookie
    if referer:
        headers['Referer'] = referer
    return headers

def dumpResponse(response):
    with open("response.html", "w", encoding="utf-8") as f:
        f.write(response)

def get_CityName():
    timestamp = str(int(round(time.time() * 1000)))
    # https://wgeo.weather.com.cn/ip/?_=1738810663478
    url = 'http://wgeo.weather.com.cn/ip/?_='+timestamp
    try:
        res = requests.get(url, headers=create_headers())
    except:
        print(" [!]正在进行网络自检并重试")
        try:
            res = requests.get(url, headers=create_headers('', 'http://www.weather.com.cn'))
        except:
            print(" [!]无法从相关网站获得请求(请求总时长：25s)，退出脚本")
            sys.exit(1)

    res = res.content.decode('utf-8')
    City = re.findall('addr="(.*?)"', res)
    # print(res)
    if City == []:
        print(' [!] 未自动匹配到你所在地的地区信息')
    else:
        CityName = "".join(City).split(',')[-1]
        #ip=re.findall('ip:"(.*?)"', res)
        code = re.findall('id="(.*?)"', res)
        return CityName, code[0]
    return "", ""


def get_city_code(city):
    try:
        url = "https://j.i8tq.com/weather2020/search/city.js"
        raw_content = requests.get(url).text
        raw_data = json.loads(raw_content[15:])
        #递归查找"NAMECN"是"[city]"的AREAID
        def find_city_by_name(name, data):
            for k, v in data.items():
                if k == "NAMECN" and v == name:
                    return data
                if isinstance(v, dict):
                    result = find_city_by_name(name, v)
                    if result:
                        return result
            return None
        city = find_city_by_name(city, raw_data)
        return city['AREAID']
    except Exception as Error:
        print(' [!] 错误，未能找到该地区信息')
        print(" [#] 退出脚本")
        #raise Error
        sys.exit()


def get_weaPage(url, headers):
    res = requests.get(url, headers=headers)
    # print(res.text)
    s = res.content.decode('utf-8')
    bs = bs4.BeautifulSoup(s, "html.parser")
    html = bs.prettify()
    return html


def CheckInput(InputString):
    if any(char.isdigit() for char in InputString) or InputString.isspace():
        return True
    match = re.search('[a-zA-Z]+$', InputString)
    if match:
        return True
    return False

def get_weather(City_code):
    # timestamp的长度为13
    # timestamp = ''.join(str(random.choice(range(10))) for i in range(13))
    t = time.time()
    timestamp = str(int(round(t * 1000)))
    port = "http://d1.weather.com.cn/weather_index/"+City_code+".html?_="+timestamp
    html = get_weaPage(port, create_headers('', 'http://www.weather.com.cn'))
    dumpResponse(html)
    # print(html)
    wea_list_all = html.split("var")
    # print(wea_list_all)

    temp_port = "http://d1.weather.com.cn/dingzhi/"+City_code+".html?_="+timestamp
    temp_html = get_weaPage(temp_port, create_headers('', 'http://www.weather.com.cn'))

    # -----------------------------------------------------

    # 温度区间:maxtemp,mintemp
    # print(temp_html)
    temp_data = re.findall(r'"weatherinfo":{(.*?)}', temp_html)
    temp_json = '{'+temp_data[0]+'}'
    # print(temp_json)
    temp_json = json.loads(temp_json)

    maxtemp = temp_json['temp']
    mintemp = temp_json['tempn']

    # dataSK
    # -----------------------------------------------------
    wea_list3 = re.findall(r' dataSK ={(.*?)}', wea_list_all[3])
    wea_list3 = '{'+wea_list3[0]+'}'
    wea_list3_json = json.loads(wea_list3)
    # print(wea_list3_json)

    # 城市英文
    city_en = wea_list3_json['nameen']
    # 城市
    cityname = wea_list3_json['cityname']
    # 实时天气
    wea_now = wea_list3_json['weather']
    # 当前温度
    temp_now = wea_list3_json['temp']
    # 湿度
    wet = wea_list3_json['SD']
    # 时间
    update = wea_list3_json['time']
    # 空气质量
    aqi = wea_list3_json['aqi']
    # PM2.5
    aqi_pm25 = wea_list3_json['aqi_pm25']
    # 日期
    date = wea_list3_json['date']
    # -----------------------------------------------------

    # dataZS
    wea_list4 = re.findall(r'"zs":{(.*?)}', wea_list_all[4])
    wea_list4 = '{'+wea_list4[0]+'}'
    wea_list4_json = json.loads(wea_list4)
    # print(wea_list4_json)
    umbrella = wea_list4_json['ys_des_s']

    # 和风天气
    qwea_url = "https://www.qweather.com/weather/"+city_en+"-"+City_code+".html"
    qwea_html = get_weaPage(qwea_url, create_headers())
    # print(qwea_html)

    wea_comment = re.findall(
        r'<div class="current-abstract">(.*?)</div>', qwea_html, re.S)
    wea_comment = "".join(wea_comment)
    aqi_level = re.findall(
        r'<p class="city-air-chart__txt text-center">(.*?)</p>', qwea_html, re.S)
    aqi_level = aqi_level[0].strip()
    wea_comment = wea_comment.strip()

    # -----------------------------------------------------
    weather_text = ''' {0}

 ===================================
 定位城市:  {1}
 实时天气:  {2}
 体感温度:  {3}℃
 温度区间:  {4} ~ {5}
 空气湿度:  {6}
 空气质量:  {7}({8}),PM2.5: {9}
 雨具携带:  {10}
 [更新时间: {11} {12}]
 ==================================='''.format(wea_comment, cityname, wea_now, temp_now, maxtemp,
                                               mintemp, wet, aqi, aqi_level, aqi_pm25, umbrella, date, update)

    # alarmDZ
    # -----------------------------------------------------
    weather_text += "\n".join(weather_alarm(wea_list_all[2]))
    #print(weather_text)
    return weather_text

def weather_alarm(alarm_list):
    json_str = re.search(r"alarmDZ\s*=\s*(\{.*\});", alarm_list, re.DOTALL).group(1)
    alarmDZ = json.loads(json_str)
    if alarmDZ["w"] == []:
        return
    yield ("\n [!]气象部门发布" + str(len(alarmDZ["w"])) + "则预警,请注意:")
    for alarm, id in enumerate(alarmDZ["w"]):
        content = id["w9"].replace("：", ":\n ", 1)
        yield (" [" + str(alarm + 1) + "]" + content)
        yield (
            " \t[=]详情: https://www.weather.com.cn/alarm/newalarmcontent.shtml?file="
            + id["w11"]
        )

def main_weather_process(output=0):
    try:
        address, code = get_CityName()
        if len(address) == 0:
            address = input(" [?] 请手动输入所在地（例：广州）[输入为空即退出]：")
            if address == "":
                print(" [#] 退出脚本")
                sys.exit(1)
            else:
                if CheckInput(address):
                    print(" [!]检测非地名字符，退出脚本")
                    sys.exit(1)
                else:
                    print(" [+] 使用手动输入定位位置："+address)
                    code = get_city_code(address)
        else:
            print(" [+] 自动定位位置："+address)

        try:
            weather_text = get_weather(code)
            if output == 0:
                print("\n"+weather_text+"\n")
                # os.system("pause")
            elif output == 1:
                from tkinter import Tk, Text, INSERT
                windows = Tk()
                windows.title("GetWeather")
                text1 = Text(windows)
                text1.insert(INSERT, weather_text)
                text1.pack()
                windows.mainloop()
        except Exception as Error:
            print(' [!] 未能找到该地区的天气信息')
            print(" [#] 退出脚本")
            raise Error
            sys.exit()
    except Exception:
        raise


def debug_mode(city):
    """
    Debug Mode: 检测指定城市的所有相关 URL 的状态码。
    """
    urls = [
        f"https://j.i8tq.com/weather2020/search/city.js",
        f"http://d1.weather.com.cn/weather_index/{city}.html",
        f"http://d1.weather.com.cn/dingzhi/{city}.html"
    ]
    results = []  # 用于存储状态码结果

    for url in urls:
        try:
            response = requests.get(url, headers=create_headers(), timeout=10)
            # 打印状态码并存储结果
            print(f"URL: {url}, Status Code: {response.status_code}")
            results.append({"url": url, "status_code": response.status_code})
        except Exception as e:
            # 捕获异常并记录
            print(f"Error fetching URL: {url}, Exception: {e}")
            results.append({"url": url, "error": str(e)})

    # 将结果保存到文件
    with open("debug_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    print("Debug results saved to debug_results.json")

if __name__ == '__main__':
    
    # 改动 2：支持命令行参数解析
    parser = argparse.ArgumentParser(description="Weather Script with Debug Mode")
    parser.add_argument("--debug", action="store_true", help="启用 Debug 模式，仅检查状态码")
    parser.add_argument("--city", type=str, default="101280601", help="城市代码 (默认: 广州)")
    parser.add_argument("--output", type=int, default=0, help="输出模式，0为shell输出，1为窗口输出(窗口仅输出天气信息)")
    args = parser.parse_args()

    # 改动 3：根据参数选择运行模式
    if args.debug:
        debug_mode(args.city)
    else:
        output = args.output
        main_weather_process(output)
