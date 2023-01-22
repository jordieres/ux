#! /usr/bin/python3
#
import os, sys, requests, json
#
headers = {
    "Content-Type": "application/json"
}
#
dur  = 12
area = 1000
wdth = 945
wgth = 16.5
thick= 0.12
#
coil = {
     "Duration": dur,
     "area": area,
     "(VA) width": wdth,
     "(VA) weight": wgth,
     "(VA) thickness": thick
}
#
res = requests.post('https://apiict00.etsii.upm.es/dynreact/predict-e.py',\
     data=json.dumps(coil), headers=headers)
print(res.json())
