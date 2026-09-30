import re
import bs4
import requests
import time

headers = {
    'Referer' : "http://www.weather.com.cn",
    'Cookie': '',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0'
    }

def get_weaPage(url):
    
    headers = {
    'Referer' : "http://www.weather.com.cn",
    'Accpet' : 'json',
    'Cookie': '',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0'
    }
    res = requests.get(url, headers=headers)
    #print(html.text)
    s=res.content
    s.decode('ISO-8859-1')
    bs = bs4.BeautifulSoup(s,"html.parser")
    html = bs.prettify()
    return html

t = time.time()
timestamp = str(int(round(t * 1000)))

port = "http://d1.weather.com.cn/calendar_new/2022/101010100_202210.html?_="+timestamp
html = get_weaPage(port)
print(html)
wea_list_all= html.split("var")
print(wea_list_all)
#print(wea_list[1]) #cityDZ
#print(wea_list[2]) #alarmDZ!
#print(wea_list[3]) #dataSK
#print(wea_list[4]) #dataZS!