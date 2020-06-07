import cv2
import numpy as np
import time
import pytesseract
import shutil
import os
import random

def zonas(img):#leo un archivo imagen en gris
    
    img = cv2.resize(img, (1200,1000))#reescalo 

    #RECORTE INCIAL: Por zona aproximada - rectángulos de mediciones, rectágulo de alarmas y rectángulo de gráficos
    zonamed = img[60:710, 0:160] #zona mediciones
    zonaalarm = img[720:900, 0:1200] #zona alarmas
    zonagraf = img[60:740, 160:1200] #zona gráficos
    zonamodo= img[0:80, 15:500]      #zona modo
    zonatipog= img[0:80, 500:700]    #zona tipo de gráfico
    
    return [zonamed,zonaalarm,zonagraf,zonamodo,zonatipog]

def modo(zonamodo):
    zonamodo = cv2.cvtColor(zonamodo, cv2.COLOR_BGR2GRAY)
    zmodo= cv2.bitwise_not(zonamodo)
    #zmodo = cv2.adaptiveThreshold(zmodo, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 4)
    #zmodo = cv2.medianBlur(zmodo, 5,5) #blur para emparejar
    texto = pytesseract.image_to_string(zmodo, config='-l eng --oem 3 --psm 6') #talves es 6 en vez de 11
    texto = texto.lower() #paso a minúsculas
    listamodos = ["pressure", "volume", "tcpl"]
    i=0
    m=2 #Error al encontrar el modo
    puntajemax=0
    for modo in listamodos:  #asigno puntaje de coincidencia y veo con qué modo es más alto este puntaje
        puntaje=0
        for char in modo:
          for letra in texto:
            if char==letra:
                puntaje=puntaje +1
          if puntaje>puntajemax:
            puntajemax=puntaje
            m=modo
    return m

def modo_g(zonatipog):
    zonatipog = cv2.cvtColor(zonatipog, cv2.COLOR_BGR2GRAY)
    zmodo= cv2.bitwise_not(zonatipog)
    zmodo = cv2.adaptiveThreshold(zmodo, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 4)
    texto = pytesseract.image_to_string(zmodo, config='-l eng --oem 3 --psm 6') #talves es 6 en vez de 11
    texto = texto.lower() #paso a minúsculas

    listatipos = ["main", "trends", "loops"]
    i=0
    m="Error al detectar el tipo de gráfico"
    puntajemax=0
    t=2
    for tipo in listatipos:  #asigno puntaje de coincidencia y veo con qué modo es más alto este puntaje
        puntaje=0
        for char in tipo:
            for letra in texto:
                if char==letra:
                    puntaje=puntaje +1
            if puntaje>puntajemax:
                puntajemax=puntaje
                t=tipo
    return t

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

def alarmas(zonaalarm,modo):
    zonaa = cv2.cvtColor(zonaalarm, cv2.COLOR_BGR2GRAY)
    zonaa= cv2.bitwise_not(zonaa)
    clahe = cv2.createCLAHE(clipLimit=0.0, tileGridSize=(1,1)) ##aumento de contraste
    zona = clahe.apply(zonaa)
    zona = cv2.blur(zona, (9, 9),) # Blur
    #Reconocimiento círculos de área afín y ubicación 
    detected_circles = cv2.HoughCircles(zona, cv2.HOUGH_GRADIENT, 1, 60, param1 = 50, param2 = 30, minRadius = 50, maxRadius = 70)
    val = [] 
    if detected_circles is not None: # Draw circles that are detected
      detected_circles = np.uint16(np.around(detected_circles))   # Convert the circle parameters a, b and r to integers. 
      for pt in detected_circles[0, :]: 
        a, b, r = pt[0], pt[1], pt[2] 
        rval= zonaa[b-25:b+45, a-50:a+50] #recorto solo valor del número dentro de cada círculo
        #PreprocesamientoLectura
        rval = cv2.adaptiveThreshold(rval, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY,17 , 8)
        rval= cv2.medianBlur(rval, 5) #blur para emparejar
        kernel = np.ones((3,3),np.uint8) #ventana de los siguientes filtros
        rval= cv2.dilate(rval, kernel, iterations = 1)#pongo flaquito
        #Lectura
        vals = pytesseract.image_to_string(rval, config='-l eng --oem 3 --psm 6') # decodificar imagen
        val.append([a, vals]) #agregar valor al final de la lista 

    val.sort() #ordena los valores de izquierda a derecha
    #ALMACENAMIENTO Y ASIGNACIÓN DE VALORES A VARIABLES SEGUN MODO
    if modo == "volume":
      mensajealarmas = ["Rate: "+ val[0][1]+" rpm", "Volume: "+ val[1][1]+" mL", "Peak Flow: "+val[2][1]+" L/min", "Insp Pause: "+ val[3][1]+ " rpm", "PEEP: "+ val[4][1]+ " cmH2O", "Flow Trig: "+ val[5][1]+ " L/min",  "FIO2: "+ val[6][1]+ " %"]
    elif modo == "tcpl":
      mensajealarmas = ["Rate: "+ val[0][1]+" rpm", "Ins Press: "+ val[1][1]+" cmH2O", "Peak Flow: "+val[2][1]+" L/min", "Insp Time: "+ val[3][1]+ " sec", "PEEP: "+ val[4][1]+ " cmH2O", "Flow Trig: "+ val[5][1]+ " L/min",  "FIO2: "+ val[6][1]+ " %"]
    elif modo == "pressure":
      mensajealarmas = ["Rate: "+ val[0][1]+" rpm", "Insp Pres: "+ val[1][1]+" cmH2O", "Insp Time: "+ val[2][1]+ " sec", "PEEP: "+ val[3][1]+ " cmH2O", "Flow Trig: "+ val[4][1]+ " L/min",  "FIO2: "+ val[5][1]+ " %"]

    else: 
      mensajealarmas = "modo invalido"
      
    return mensajealarmas

def graficos(zonagraf,mode):
#     zonagraf = cv2.cvtColor(zonagraf, cv2.COLOR_BGR2GRAY)
#     zona= cv2.bitwise_not(zonagraf)
#     zonath = cv2.adaptiveThreshold(zona, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY,11 , 2)
#     grafl = cv2.medianBlur(zonath, 5) #blur para emparejar
#     kernel = np.ones((3,3),np.uint8) #ventana de los siguientes filtros
#     grafl= cv2.dilate(grafl, kernel, iterations = 1)#dil
#     grafl= cv2.erode(grafl, kernel, iterations = 1)#dil
# 
    #Recorte según tipo de gráfico
    if mode=="trends":
        return zonagraf[0:385, 0:1040]
    
    elif mode=="main":
        return zonagraf[0:680, 0:1040]
    
    elif mode=="loops":  #debo corregirlo arriba después
        return zonagraf[0:650, 0:1040]

def mediciones(zonamed):
    zonamed=cv2.cvtColor(zonamed, cv2.COLOR_BGR2GRAY)
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

      val = pytesseract.image_to_string(rval, config='-l eng --oem 3 --psm 6') #
      #Lectura variable
      rvar = med[85:, 0:]
      rvar = cv2.adaptiveThreshold(rvar, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 19, 8)
      rvar = cv2.medianBlur(rvar, 5) #blur para emparejar
    
      var = pytesseract.image_to_string(rvar, config='-l eng --oem 3 --psm 6') #
      var = var.lower()
      #Sacar por contexto la variable
      var = SacaPorContextoM(var)
      #Formación mensaje
      mensajemed.append(var+":"+ val)
      y=int(y+h+3) #un quinto de la altura
      i=i+1
    return mensajemed

def mensaje(modo,alarmas,mediciones):
    mensaje={}
    mensaje["var1"]="modo="+modo
    msj=alarmas+mediciones
    var="var"
    aux=2
    r=len(msj)
    u=0
    while len(msj)>u:
        mensaje[var+str(aux)]=msj[u]
        aux=aux+1
        u=u+1
        
    return mensaje



