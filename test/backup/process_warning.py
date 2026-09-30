import re
import json

def weather_alarm(alarm_list):
    with open("alarm1.json", "r", encoding="utf-8") as f:
        alarmDZ = f.read()
        json_str = re.search(r'alarmDZ\s*=\s*(\{.*\});', alarmDZ, re.DOTALL).group(1)
        alarmDZ = json.loads(json_str)
        if alarmDZ['w'] == []:
            return
        yield (" [!]气象部门发布"+ str(len(alarmDZ['w'])) +"则预警,请注意:")
        for alarm,id in enumerate(alarmDZ['w']):
            content = id['w9'].replace("：", ":\n ", 1)
            yield (" ["+ str(alarm+1) +"]"+content)
            yield (" \t[=]详情: https://www.weather.com.cn/alarm/newalarmcontent.shtml?file="+id['w11'])
    
if __name__ == "__main__":
    text = weather_alarm("alarm.json")
    weather_text = "xxx\n"
    weather_text += "\n".join(text)
    print(weather_text)