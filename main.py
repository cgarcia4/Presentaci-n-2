##Test
import gamma as Gamma
import client as client
import led as led
import procesamiento as pr
import cv2
import numpy as np
import time
import io
from gpiozero import LED

        
normal= LED(22)
cam = LED(27)
net = LED(17)

estado = [normal,cam,net]
try:
  cam=Gamma.camera_init()
  led.leds(estado,1)
except:
  print("An exception occurred")
  led.leds(estado,2)


T=time.time()
a=1
gamma=1.5
while time.time()-T<60:
    #cam=Gamma.camera_init()
    time.sleep(1)
    im=Gamma.camera_take(cam)
    cv2.imwrite("input.jpg",im)
    gamma=Gamma.choice(im,gamma-0.5)
    recorte = Gamma.recorte(im,gamma)
    recorte = cv2.rotate(recorte, cv2.ROTATE_180)

    cv2.imwrite("output_"+str(a)+".jpg",recorte)
    zonas=pr.zonas(recorte)
    modo=pr.modo(zonas[3])
    modo_g=pr.modo_g(zonas[4])
    grafico=pr.graficos(zonas[2],modo_g)
    client.enviar_img(grafico)
#     
#     alarmas=pr.alarmas(zonas[1],modo)
#     cv2.imshow("",zonas[0])
#     cv2.waitKey(0)
#     mediciones = pr.mediciones(zonas[0])
#     mensaje=pr.mensaje(modo,alarmas,mediciones)
#     client.enviar_data(mensaje)
    #cv2.imwrite("output_"+str(a)+".jpg",recorte)             #Guardo la imagen resultante   
    
    #a=a+1
#
print(time.time())
