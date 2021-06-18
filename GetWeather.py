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
    except Exception as Error:
        raise Error

def get_weaPage(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0'}
    res = requests.get(url, headers=headers)
    #print(html.text)
    s=res.content
    s.decode('ISO-8859-1')
    bs = bs4.BeautifulSoup(s,"html.parser")
    html = bs.prettify()
    return html

def get_weather(City_code):
    port1 = "http://www.weather.com.cn/data/cityinfo/"+City_code+".html"
    port2 = "http://www.weather.com.cn/data/sk/"+City_code+".html"
    
    html1 = get_weaPage(port1)
    wea_list1 = html1.split(",")
    #最高温度
    high_temp = wea_list1[2]
    high_temp = re.findall(r'"temp1":"(.*?)"',high_temp)
    high_temp = "".join(high_temp)
    #最低温度
    low_temp = wea_list1[3]
    low_temp = re.findall(r'"temp2":"(.*?)"',low_temp)
    low_temp = "".join(low_temp)
    #天气状况
    wea_state = wea_list1[4]
    wea_state = re.findall(r'"weather":"(.*?)"',wea_state)
    wea_state = "".join(wea_state)

    #实时天气
    html2 = get_weaPage(port2)
    wea_list2 = html2.split(",")
    temp_now = wea_list2[2]
    temp_now = re.findall(r'"temp":"(.*?)"',temp_now)
    temp_now = "".join(temp_now)
    #湿度
    wet = wea_list2[5]
    wet = re.findall(r'"SD":"(.*?)"',wet)
    wet = "".join(wet)
    #时间
    wea_time = wea_list2[9]
    wea_time = re.findall(r'"time":"(.*?)"',wea_time)
    wea_time = "".join(wea_time)

    print(" -------------------------")
    print(" 天气状况: "+wea_state)
    print(" 实时温度: "+temp_now+"℃")
    print(" 今日的温度区间: "+high_temp+"-"+low_temp)
    print(" 空气湿度: "+wet)
    print(" 更新时间 "+wea_time)
    print(" -------------------------")



if __name__ == '__main__':
    try:
        address = get_CityName()
        if len(address) ==0:
             address = input(" [?] 请手动输入所在地（例：广州）[输入为空即退出]：")
             if len(address) ==0:
                 exit
             else:
                 print(" [+] 使用手动输入定位位置："+address)
        else:
             print(" [+] 自动定位位置："+address) 
        code = get_city_code(address)
        get_weather(code)

    except:
        print(" [!] 定位失败")