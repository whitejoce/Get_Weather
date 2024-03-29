
# Get_Weather
 
 * 关于
      
      本代码仓库采用MIT许可协议（[The MIT License](https://github.com/whitejoce/Get_Weather/blob/main/LICENSE)）
      
      我的Code代码仓库整合了此脚本,添加了查询城市天气(生活助手):[LifeHelper.py](https://github.com/whitejoce/Code/blob/main/Code/LifeHelper.py)
      
      > 基于本项目的[安卓APP Demo](https://github.com/whitejoce/Code/tree/main/Andorid/NewWeather)
     
      
* * *

* GetWeather.py
 
    <p align="left">
     <a href="https://docs.python.org/3/download.html">
       <img src="https://img.shields.io/badge/Python-3.x-green.svg">
     </a>
   </p>
  
  >要求安装`requests,BeautifulSoup`库

* * *

*   实现方法：

    > 通过获取定位（定位到市级），爬取当地的天气。
    > 
    > 脚本中采用的接口不同于网上（网上的的接口天气不更新了），应该是“全网首发”     ; )
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
   >以此数据结构为例：
         `[alarmDZ,dataSK,dataZS]`

         
         dataSK ={
         
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
                  "date":"06月19日(星期六)"           #日期
                };
                
          
         #分两种格式（有无预警）
         1，alarmDZ ={"w":[]};
         
         2，alarmDZ ={
                  "w":[{
                  "w1":"北京市",
                  "w2":"",
                  "w3":"",
                  "w4":"07",
                  "w5":"高温",
                  "w6":"01",
                  "w7":"蓝色",
                  "w8":"2021-06-18 15:41",
                  "w9":"市气象台2021年6月18日15时45分发布高温蓝色预警信号：预计，19日至20日，本市大部分地区日最高气温将在35℃以上，请注意防范。（预警信息来源：国家预警信息发布中心）",
                  "w10":"202106181541545112高温蓝色",
                  "w11":"10101-20210618154146-0701.html",
                  "w12":"2021-06-18 15:44",
                  "w13":"北京市发布高温蓝色预警"}]
                  };
                  
                  
           #各种指数
           dataZS ={"zs":{
                  "date":"2021061918",
                  "lk_name":"路况指数","lk_hint":"干燥","lk_des_s":"天气较好，路面较干燥，路况较好。",
                  "cl_name":"晨练指数","cl_hint":"较适宜","cl_des_s":"请选择避风的地点晨练，避免迎风锻炼。",
                  "gj_name":"逛街指数","gj_hint":"适宜","gj_des_s":"这种好天气去逛街可使身心畅快放松。",
                  "pl_name":"空气污染扩散条件指数","pl_hint":"中","pl_des_s":"易感人群应适当减少室外活动。",
                  "co_name":"舒适度指数","co_hint":"舒适","co_des_s":"白天温度宜人，风力不大。",
                  "pj_name":"啤酒指数","pj_hint":"适宜","pj_des_s":"天气炎热，可适量饮用啤酒，不要过量。",
                  "hc_name":"划船指数","hc_hint":"适宜"，"hc_des_s":"天气较好，适宜划船及嬉玩水上运动。",
                  "gl_name":"太阳镜指数","gl_hint":"很必要","gl_des_s":"建议佩戴透射比2级且UV400的遮阳镜",
                  "uv_name":"紫外线强度指数","uv_hint":"很强","uv_des_s":"涂擦SPF20以上，PA++护肤品，避强光。",
                  "wc_name":"风寒指数","wc_hint":"无","wc_des_s":"温度未达到风寒所需的低温，稍作防寒准备即可。",
                  "ct_name":"穿衣指数","ct_hint":"热","ct_des_s":"适合穿T恤、短薄外套等夏季服装。",
                  "pk_name":"放风筝指数","pk_hint":"较适宜","pk_des_s":"气温略高，放风筝时戴上太阳帽。",
                  "ac_name":"空调开启指数","ac_hint":"较少开启","ac_des_s":"体感舒适，不需要开启空调。",
                  "dy_name":"钓鱼指数","dy_hint":"较适宜","dy_des_s":"风稍大会对垂钓产生一定影响。",
                  "ls_name":"晾晒指数","ls_hint":"极适宜","ls_des_s":"天气不错，抓紧时机让衣物晒太阳吧。",
                  "gm_name":"感冒指数","gm_hint":"少发","gm_des_s":"感冒机率较低，避免长期处于空调屋中。",
                  "xc_name":"洗车指数","xc_hint":"适宜","xc_des_s":"天气较好，适合擦洗汽车。",
                  "tr_name":"旅游指数","tr_hint":"适宜","tr_des_s":"天气较好，可尽情地享受大自然的风光。",
                  "nl_name":"夜生活指数","nl_hint":"较适宜","nl_des_s":"只要您稍作准备就可以放心外出。",
                  "xq_name":"心情指数","xq_hint":"好","xq_des_s":"好天气会带来一天的好心情。",
                  "yh_name":"约会指数","yh_hint":"较适宜","yh_des_s":"不用担心天气来调皮捣乱而影响了兴致。",
                  "yd_name":"运动指数","yd_hint":"适宜","yd_des_s":"天气较好，尽情感受运动的快乐吧。",
                  "ag_name":"过敏指数","ag_hint":"不易发","ag_des_s":"除特殊体质，无需担心过敏问题。",
                  "mf_name":"美发指数","mf_hint":"一般","mf_des_s":"注意清洁，建议选用防晒滋润型护发品。",
                  "ys_name":"雨伞指数","ys_hint":"不带伞","ys_des_s":"天气较好，不用带雨伞。",
                  "fs_name":"防晒指数","fs_hint":"极强","fs_des_s":"需涂擦SPF大于20，PA++，护肤品。",
                  "pp_name":"化妆指数","pp_hint":"去油防晒","pp_des_s":"请选用水质无油粉底霜。",
                  "zs_name":"中暑指数","zs_hint":"无中暑风险","zs_des_s":"天气舒适，对易中暑人群来说非常友善。",
                  "jt_name":"交通指数","jt_hint":"良好","jt_des_s":"气象条件良好，车辆可以正常行驶。",
                  "gz_name":"干燥指数","gz_hint":"非常干燥","gz_des_s":"空气干燥，极易引起皮肤水分流失，建议涂抹防晒霜，多喝水保持身体滋润。"},
                  "cn":"北京"
                  };




