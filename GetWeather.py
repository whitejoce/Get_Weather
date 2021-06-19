import sys
import json
import random
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
    except Exception as Error:
        raise Error

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
    
    #num_str的长度为13
    num_str = ''.join(str(random.choice(range(10))) for i in range(13))
    port = "http://d1.weather.com.cn/sk_2d/"+City_code+".html?_="+num_str

    html1 = get_weaPage(port)
    wea_list= html1.split(",")
    #城市
    cityname = wea_list[1]
    cityname = re.findall(r'"cityname":"(.*?)"',cityname)
    cityname = "".join(cityname)
    #当前温度
    temp_now = wea_list[3]
    temp_now = re.findall(r'"temp":"(.*?)"',temp_now)
    temp_now = "".join(temp_now)
    #实时天气
    wea_now = wea_list[18]
    wea_now = re.findall(r'"weather":"(.*?)"',wea_now)
    wea_now = "".join(wea_now)
    #湿度
    wet = wea_list[9]
    wet = re.findall(r'"SD":"(.*?)"',wet)
    wet = "".join(wet)
    #PM2.5
    aqi_pm25 = wea_list[17]
    aqi_pm25 = re.findall(r'"aqi_pm25":"(.*?)"',aqi_pm25)
    aqi_pm25 = "".join(aqi_pm25)
    #降雨指数
    #rain = wea_list[14]
    #rain = re.findall(r'"rain":"(.*?)"',rain)
    #rain = "".join(rain)
    #rain24h = wea_list[15]
    #rain24h = re.findall(r'"rain24h":"(.*?)"',rain24h)
    #rain24h = "".join(rain24h)
    #时间
    time = wea_list[13]
    time = re.findall(r'"time":"(.*?)"',time)
    time = "".join(time)
    #日期
    date = wea_list[22]#22
    date = re.findall(r'"date":"(.*?)"',date)
    date = "".join(date)


    print(" =================================")
    print(" 定位城市:  "+cityname)
    print(" 天气状况:  "+wea_now)
    print(" 实时温度:  "+temp_now+"℃")
    print(" 空气湿度:  "+wet)
    #print(" 降雨概率:  "+rain +"% ,24小时内降水: "+rain24h+"%")
    print(" PM2.5指数: "+aqi_pm25)
    print(" [更新时间: "+date+" "+time +"]")
    print(" =================================")



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

    except:
         pass
