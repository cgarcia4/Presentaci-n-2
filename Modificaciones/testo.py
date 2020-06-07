import cv2
import numpy as np
import time
import pytesseract
import shutil
import os
import random

img = cv2.imread('output_1.jpg',0) #leo un archivo imagen en gris
img = cv2.resize(img, (1200,1000))
zonamed = img[60:710, 0:160] #zona mediciones
cv2.imshow("",zonamed)
cv2.waitKey(0)
zonaalarm = img[720:900, 0:1200] #zona alarmas
zonagraf = img[60:740, 160:1200] #zona gráficos
zonamodo= img[0:80, 15:500]      #zona modo
zonatipog= img[0:80, 500:700]    #zona tipo de gráficdef SacaPorContextoM(texto):


def SacaPorContextoM(texto):
  i=0
  puntajemax=0
  if len(texto)>3:     #el texto el largo
    listavariables = ["ppeak", "rate","total", "vti/kg", "fio2"]
    for variable in listavariables:
      puntaje=0
      for char in variable:
        for letra in texto:
          if char==letra:
            puntaje=puntaje +1
      if puntaje>puntajemax:
        puntajemax=puntaje
        var=variable
  else:                #el texto es cortito
    listavariables = ["vti", "vtie", "fio2"]
    for variable in listavariables:
      puntaje=0
      for char in variable:
        for letra in texto:
          if char==letra:
            puntaje=puntaje +1
      if puntaje>puntajemax:
        puntajemax=puntaje
        var=variable
  return var

mensajemed=[]
#Preprocesamiento
zona= cv2.bitwise_not(zonamed)
zonath = cv2.threshold(zona, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1] #para distinguir cuadraditos
zonath = cv2.medianBlur(zonath, 5) #blur para emparejar
kernel = np.ones((5,5),np.uint8) #ventana de los siguientes filtros
zonath= cv2.erode(zonath, kernel, iterations = 4)#erosion
#Recorte
coords = np.column_stack(np.where(zonath ==[0]))  #[[x1 y1] [x2 y2] ....] cordenadas de pixeles negros
ymin=700
ymax=0
xmin=200
for c in coords: #[xi yi]
  y=c[0]
  x=c[1]
  if x==80: #busco desde la mitad 
    if y< ymin:  #busco el primer pixel negro de arriba hacia abajo
      ymin=y
    if y> ymax: #busco el ultimo pixel negro de arriba hacia abajo
      ymax=y
  if x< xmin:  #busco el primer pixel negro de izquierda a derecha
    xmin=x
h= int((ymax -ymin)*0.2) #altura de cada rectángulo es la altura total dividida en 5
y=ymin
i=1
while i<=5:
  med = zona[y:y+h, xmin:145] #recorto la imágen gris
  #Lectura número
  rval=med[0:60, 0:]
  rval = cv2.adaptiveThreshold(rval, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 8)
  rval = cv2.medianBlur(rval, 5) #blur para emparejar
  kernel = np.ones((3,3),np.uint8) #ventana de los siguientes filtros
  rval= cv2.dilate(rval, kernel, iterations = 1)#erosion
  rval= cv2.erode(rval, kernel, iterations = 1)#dil
  cv2.imshow("",rval)
  cv2.waitKey(0)
  val = pytesseract.image_to_string(rval, config='-l eng --oem 3 --psm 6') #
  #Lectura variable
  rvar = med[85:, 0:]
  rvar = cv2.adaptiveThreshold(rvar, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 19, 8)
  rvar = cv2.medianBlur(rvar, 5) #blur para emparejar
  cv2.imshow("",rvar)
  cv2.waitKey(0)
  var = pytesseract.image_to_string(rvar, config='-l eng --oem 3 --psm 6') #
  var = var.lower()
  #Sacar por contexto la variable
  var = SacaPorContextoM(var)
  #Formación mensaje
  mensajemed.append(var+":"+ val)
  y=int(y+h+3) #un quinto de la altura
  i=i+1

