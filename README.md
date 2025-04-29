
# Get_Weather
 
 * 关于

      本代码仓库采用MIT许可协议（[The MIT License](https://github.com/whitejoce/Get_Weather/blob/main/LICENSE)）
      
      我的Code代码仓库整合了此脚本,添加了查询城市天气(生活助手):[LifeHelper.py](https://github.com/whitejoce/Code/blob/main/Code/LifeHelper.py)
      
      > 基于本项目的[安卓APP Demo](https://github.com/whitejoce/Code/tree/main/Android/NewWeather) ， [DeepWiki for this Repository](https://deepwiki.com/whitejoce/Get_Weather)
     
      
* * *

* GetWeather.py
 
    <p align="left">
     <a href="https://docs.python.org/3/download.html">
       <img src="https://img.shields.io/badge/Python-3.x-green.svg">
     </a>
   </p>
  
  > 要求安装 `requests, BeautifulSoup` 库

* * *

*   实现方法：

    > 通过获取定位（定位到市级），爬取当地的天气。
    > 
    > 脚本中采用的接口不同于网上（网上的接口天气不更新了），应该是“全网首发”     ; )
    >
    >定位接口（仅限国内）: [中国天气网](http://wgeo.weather.com.cn/ip/);
    >
    > 天气数据来源网站: [中国天气网](http://www.weather.com.cn/),[和风天气](https://www.qweather.com/)；

* * *

*   使用方法:
    
     `~$: python GetWeather.py`

* * *




* 代码效果：

      
           今天白天晴，夜晚晴，温度和昨天差不多，现在35°，有风，空气不错。

           ==================================
           定位城市:  北京
           实时天气:  晴
           实时温度:  35℃
           温度区间:  21℃ - 36℃
           空气湿度:  15%
           空气质量:  31(优),PM2.5: 31
           雨具携带:  天气较好，不用带雨伞。
           [更新时间: 06月20日(星期日) 12:50]
           ==================================
           [!]气象部门发布预警,请注意:
           [1]市气象台2021年6月18日15时45分发布高温蓝色预警信号:
           预计，19日至20日，本市大部分地区日最高气温将在35℃以上，请注意防范。（预警信息来源：国家预警信息发布中心）
       
* * *
 * 接口信息：

   >提供接口的相关信息，供大家自定义天气窗口
   >
   > 接口:`http://d1.weather.com.cn/weather_index/`[城市ID]`.html?_=`[时间戳(毫秒)]
   >
   
   详细API说明: [API.md](./API.md)
