#!/usr/bin/env python
# _*_coding: utf-8 _*_
#Coder:Whitejoce

import json
import re

if __name__ == '__main__':
    
    with open('response.html', 'r', encoding='utf-8') as f:
        data = f.read()
        #print(data)
        
        data = data.split(';')[:-1]
        print(data)
        # var cityDZ =
        for d in data:
            format_data = re.findall(r'=(.*?);', data+';')
            for i in enumerate(format_data):
                print(i, json.loads(i[1]))