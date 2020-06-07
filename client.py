from __future__ import print_function
import requests
import json
import time
import cv2

def enviar_img(img, url= 'http://127.0.0.1:5000/VMPaciente/video'):
    content_type = 'output_1.jpg'
    headers = {'content-type': content_type}# prepare headers for http request
    _, img_encoded = cv2.imencode('.jpg', img)# encode image as jpeg
    requests.post(url, data=img_encoded.tostring(), headers=headers)
    return 0

def enviar_data(mensaje,url = 'http://127.0.0.1:5000/VMPaciente/mensajes'):
    mensajejson= json.dumps(mensaje)
    r = requests.post(url, data=mensajejson)
    return 0
    

            

 