# Get_Weather

* GetWeather.py
 
    Python版本: 3.x

* * *

*   实现方法：

    > 通过获取IP定位，爬取当地的天气。
    > 
    > 脚本中采用的接口不同于网上（网上的的接口天气不更新了），应该是“全网首发”   ; )
    >
    > 天气来源网站[Weather](http://www.weather.com.cn/)；

* * *

*   使用方法:
    
     `~$: python ./GetWeather.py`

* * *




* 效果：

       =================================
       定位城市:  上海
       天气状况:  阴
       实时温度:  20℃
       空气湿度:  94%
       PM2.5指数: 24
       [更新时间: 06月19日(星期六) 11:10]
       =================================
       
* * *
   >提供接口的相关信息，供大家自定义天气窗口
   >
   > 接口1:`http://d1.weather.com.cn/weather_index/`[城市ID]`.html?_=`[时间戳(毫秒)]
   >
   > 接口2:`http://d1.weather.com.cn/dingzhi/`[城市ID]`.html?_=`[时间戳(毫秒)]
   >
   > 接口3(v2.0使用):`http://d1.weather.com.cn/sk_2d/`[城市ID]`.html?_=`[时间戳(毫秒)]
   >
   >以此数据结构为例：
        
        dataSK={
                  dataSK={
                  "nameen":"beijing",                #城市英文名
                  "cityname":"北京",                 #城市名称
                  "city":"101010100",                #城市编号
                  "temp":"32",                       #摄氏度
                  "tempf":"89",                      #华氏度
                  "WD":"北风",                       #风向
                  "wde":"N",                         #风向（字母表示）
                  "WS":"1 级",                       #风力
                  "wse":"4km/h",                     #风速
                  "SD":"13%",                        #湿度
                  "sd":"13%",
                  "qy":"994",                        #气压
                  "njd":"26km",                      #能见度
                  "time":"09:40",                    #数据更新时间
                  "rain":"0",
                  "rain24h":"0",
                  "aqi":"35",                        #空气质量
                  "aqi_pm25":"35",                   #PM2.5指数
                  "weather":"晴",                    #天气状况
                  "weathere":"Sunny",                #天气状况（英语）
                  "weathercode":"d00",
                  "limitnumber":"不限行",             #城市限行
                  "date":"06月19日(星期六)",          #日期
                }


