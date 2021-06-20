import sys
import json
import requests
import bs4
import re
import urllib as urlparse
import http.client

def download_page(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0'}
    html = requests.get(url, headers=headers)
    #print(html.text)
    return html.text

def get_CityName():
    res = requests.get('http://jsonip.com')
    ip = res.json()['ip']
    #print(ip)
    ip_url = "http://mip.chinaz.com/?query="+ip
    ip_html = download_page(ip_url)
    location = re.findall(r'<td class="z-tc">(.*?)</td>',ip_html)
    #print(location)
    result = location[-1]
    City = re.findall('(.*?)市',result)
    CityName = "".join(City)
    CityName = CityName[-2:]
    if len(CityName) ==0:
             print(' [!] 未自动匹配到你所在地的地区信息:'+result)
    return CityName

def get_city_code(city):
    try:
        parameter = urlparse.parse.urlencode({'cityname': city})
        conn = http.client.HTTPConnection('toy1.weather.com.cn', 80, timeout=5)
        conn.request('GET', '/search?' + parameter)
        r = conn.getresponse()
        data = r.read().decode()[1:-1]
        json_data = json.loads(data)
        code = json_data[0]['ref'].split('~')[0]
        return code
    except:
        print(' [!] 未能找到该地区信息')
        print(" [#] 退出脚本")
        sys.exit(1)

def get_weaPage(url):
    headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0',
    }
    res = requests.get(url, headers=headers)
    #print(html.text)
    s=res.content
    s.decode('ISO-8859-1')
    bs = bs4.BeautifulSoup(s,"html.parser")
    html = bs.prettify()
    return html

def get_weather(City_code):
    import time
    #timestamp的长度为13
    #timestamp = ''.join(str(random.choice(range(10))) for i in range(13))
    t = time.time()
    timestamp = str(int(round(t * 1000)))
    port = "http://d1.weather.com.cn/weather_index/"+City_code+".html?_="+timestamp
    html = get_weaPage(port)
    wea_list_all= html.split("var")

    #cityDZ
    html1= wea_list_all[1]
    wea_list1= html1.split(",")
    #城市英文
    city_en = wea_list1[1]
    city_en = re.findall(r'"cityname":"(.*?)"',city_en)
    city_en = "".join(city_en)
    #温度区间
    maxtemp = wea_list1[2]
    maxtemp = re.findall(r'"temp":"(.*?)"',maxtemp)
    maxtemp = "".join(maxtemp)

    mintemp = wea_list1[3]
    mintemp = re.findall(r'"tempn":"(.*?)"',mintemp)
    mintemp = "".join(mintemp)
    #实时天气
    wea_now = wea_list1[4]
    wea_now = re.findall(r'"weather":"(.*?)"',wea_now)
    wea_now = "".join(wea_now)

    #alarmDZ
    wea_list2 = wea_list_all[2]
    wea_alarm_all = re.findall(r'alarmDZ ={"w":\[(.*?)\]};',wea_list2)
    warning = 0
    EmptyList = ['']
    if wea_alarm_all == EmptyList:
         pass
    else :
         warning = 1

    
    #dataSK
    html3 = wea_list_all[3]
    wea_list3= html3.split(",")
    #城市
    cityname = wea_list3[1]
    cityname = re.findall(r'"cityname":"(.*?)"',cityname)
    cityname = "".join(cityname)
    #当前温度
    temp_now = wea_list3[3]
    temp_now = re.findall(r'"temp":"(.*?)"',temp_now)
    temp_now = "".join(temp_now)
    #湿度
    wet = wea_list3[9]
    wet = re.findall(r'"SD":"(.*?)"',wet)
    wet = "".join(wet)
    #时间
    update = wea_list3[13]
    update = re.findall(r'"time":"(.*?)"',update)
    update = "".join(update)
    #空气质量
    aqi = wea_list3[16]
    aqi = re.findall(r'"aqi":"(.*?)"',aqi)
    aqi = "".join(aqi)
    #PM2.5
    aqi_pm25 = wea_list3[17]
    aqi_pm25 = re.findall(r'"aqi_pm25":"(.*?)"',aqi_pm25)
    aqi_pm25 = "".join(aqi_pm25)
    #日期
    date = wea_list3[22]#22
    date = re.findall(r'"date":"(.*?)"',date)
    date = "".join(date)

    #dataZS
    wea_list4 = wea_list_all[4]
    umbrella = re.findall(r'"ys_des_s":"(.*?)"',wea_list4)
    umbrella = "".join(umbrella)

    #和风天气
    qwea_url = "https://www.qweather.com/weather/"+city_en+"-"+City_code+".html"
    qwea_html = get_weaPage(qwea_url)
    wea_comment = re.findall(r'<p class="c-city-weather-current__abstract">(.*?)</p>',qwea_html,flags=16)
    wea_comment = "".join(wea_comment)
    aqi_level = re.findall(r'<p class="air-chart-container__aqi-level">(.*?)</p>',qwea_html,flags=16)
    aqi_level=aqi_level[0].replace("\n","")
    aqi_level=aqi_level.replace(" ","")
    #wea_comment = wea_comment.strip('\n')
    #wea_comment = wea_comment.replace(" ","") 
    print(wea_comment)

    print(" ==================================")
    print(" 定位城市:  "+cityname)
    print(" 实时天气:  "+wea_now)
    print(" 实时温度:  "+temp_now+"℃")
    print(" 温度区间:  "+mintemp+"℃ - "+maxtemp+"℃")
    print(" 空气湿度:  "+wet)
    #0~50优，51~100良，101~150轻度污染，151~200中度污染，201~300重度污染，>300严重污染
    print(" 空气质量:  "+aqi+"("+aqi_level+"),PM2.5: "+aqi_pm25)
    print(" 雨具携带:  "+umbrella)
    print(" [更新时间: "+date+" "+update +"]")
    print(" ==================================")
    if warning==1:
        print(" [!]有关部门发布气象预警,请注意:")
        wea_alarm_all = "".join(wea_alarm_all)
        wea_alarm = re.findall(r'"w9":"(.*?)"',wea_alarm_all)
        wea_alarm = "".join(wea_alarm)
        if wea_alarm == "":
            print(" [!]无法获取气象预警详情")
            option = input(" [?]显示完整数据结构?[y/n]")
            if option=="y" or option=="Y":
                #wea_alarm = wea_alarm.replace("{","")
                #wea_alarm = wea_alarm.replace("}","")
                print(wea_alarm_all)
        else:
            wea_alarm = wea_alarm.replace("：",":\n ",1)
            print(" "+wea_alarm)    

if __name__ == '__main__':
    try:
        address = get_CityName()
        if len(address) ==0:
             address = input(" [?] 请手动输入所在地（例：广州）[输入为空即退出]：")
             if len(address) ==0:
                 print(" [#] 退出脚本")
                 sys.exit(1)
             else:
                 print(" [+] 使用手动输入定位位置："+address)
        else:
             print(" [+] 自动定位位置："+address) 
        code = get_city_code(address)
        get_weather(code)

    except Exception as Error:
        raise Error