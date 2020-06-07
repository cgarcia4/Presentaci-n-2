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
a=2

aux=1
time.sleep(1)

def busqueda_pantalla(cam):
    im=Gamma.camera_take(cam)
    gamma=Gamma.choice(im,2)
    recorte = Gamma.recorte(im,gamma)
    recorte[0] = cv2.rotate(recorte[0], cv2.ROTATE_180)
    cv2.imwrite("output_"+str(a)+".jpg",recorte[0])
    zonas=pr.zonas(recorte[0])
    modo=pr.modo(zonas[3])
    modo_g=pr.modo_g(zonas[4])
    if modo==2 or modo_g==2:
        return busqueda_pantalla(cam)
    return [modo,modo_g,recorte[1]]
    

modo=0
while time.time()-T<120:
    if modo==0:
        pantalla=busqueda_pantalla(cam)
        print("tiempoo detección y analisis modo ="+str(time.time()-T))
    modo=pantalla[0]
    modo_g=pantalla[1]
    cords=pantalla[2]
    im=Gamma.camera_take(cam)
    cv2.imwrite("input.jpg",im)
    recorte = Gamma.recorte(im,0,cords)
    recorte[0] = cv2.rotate(recorte[0], cv2.ROTATE_180)
    zonas=pr.zonas(recorte[0])
    grafico=pr.graficos(zonas[2],modo_g)
    client.enviar_img(grafico)
    t=time.time()
    mediciones = pr.mediciones(zonas[0])
    alarmas=pr.alarmas(zonas[1],modo)
    
    mensaje=pr.mensaje(modo,alarmas,mediciones)
    client.enviar_data(mensaje)
    print("Demoró "+str(time.time()-t) +" en procesar las alarmas y mediciones")

print(time.time())
