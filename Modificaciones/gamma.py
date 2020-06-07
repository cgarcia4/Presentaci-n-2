import cv2
import numpy as np
import imutils
import time
from picamera.array import PiRGBArray
from picamera import PiCamera
import io
import picamera

def select(image,gamma=1):   #Función para cambiar la gamma de la imagen, en caso de mucha luz
    lookUpTable = np.empty((1,256), np.uint8)  #se crea un array de largo 256
    for i in range(256):
        lookUpTable[0,i] = np.clip(pow(i / 255.0, gamma) * 255.0, 0, 255) #cada valor de la tabla se le asigna una conversió
    return cv2.LUT(image, lookUpTable)


def choice(image,gamma=1):  #realiza un barrido para multiples valores de gamma, para corregir efecto de luz y extraer pantalla
    #print(gamma)
    im=select(image,gamma) #se aplica el valor de gamma a la imagen
    gris = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY) #blanco y negro
    gauss = cv2.GaussianBlur(gris, (5,5), 0) #filtro para el ruido
    ret,th = cv2.threshold(gauss,0,255,cv2.THRESH_BINARY) #aplico treshold para separar imagen dependiendo de la intensidad de los pixeles
    cnts = cv2.findContours(th, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE) #busco los contornos de la imagen aplicado el treshold
    cnts = imutils.grab_contours(cnts)
    cnts = sorted(cnts, key = cv2.contourArea, reverse = True)[:1] #ordena los contornos por tamaño, solo selecionando el de largo mayor
    for c in cnts:
        approx = cv2.approxPolyDP(c, 0.009 * cv2.arcLength(c, True), True)
        n = approx.ravel()                                                  #obtengo un arreglo que describe los puntos esquina del contorno
    if len(n) > 30 or n[0]==0 or cv2.contourArea(c)>1000000 or cv2.contourArea(c)<700000 : #Defino caracteristicas que me ayudan a definir si el contorno corresponde o no a una pantalla, dependiendo de las dimensiones de esta, y numero de esquinas,
        if gamma>5:
            camera=camera_init()
            imagecamera_take(camera)
            return choice(image,1)#caso que no se encuentre el valor para evitar divergencia
        return choice(image,gamma+0.05)#si no se encuentra, se vuelve a ejecutar la funcion  con un un nuevo valor
    else:
        return gamma
        
def recorte(image,gamma,pos=0):
    if pos==0:
        im_gamma =select(image,gamma)
        gris = cv2.cvtColor(im_gamma, cv2.COLOR_BGR2GRAY)
        gauss = cv2.GaussianBlur(gris, (5,5), 0)
        ret,th = cv2.threshold(gauss,0,255,cv2.THRESH_BINARY)
        cnts = cv2.findContours(th, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)
        cnts = sorted(cnts, key = cv2.contourArea, reverse = True)[:1]

        rect = np.zeros((4, 2), dtype = "float32")# array donde guardare las esquinas de la pantalla
        for c in cnts:
            approx = cv2.approxPolyDP(c, 0.009 * cv2.arcLength(c, True), True)
            n = approx.ravel()

        pts=np.zeros((int(len(n)/2),2),dtype="float32")

        for k in range (0, int((len(n)/2))): #extraigo los posibles candidatos a esquinas
            pts[k]=[n[2*k],n[2*k+1]]
            
        s= pts.sum(axis = 1)             #A partir de relaciones de maximos y minimas distancias se extraen las 4 esquinas
        rect[0] = pts[np.argmin(s)]
        rect[0][0]=rect[0][0]
        rect[2] = pts[np.argmax(s)]
        rect[2][0]=rect[2][0]

        diff = np.diff(pts, axis = 1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]
        rect[3][0]=rect[3][0]
        rect[3][0]=rect[3][0]

        #(tl, tr, br, bl) = rect #camara derecha
        (bl, br, tr, tl) = rect #camara inv
        #Se definen las distancias entre los puntos
        widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
        widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
        maxWidth = max(int(widthA), int(widthB))
        heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
        heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
        maxHeight = max(int(heightA), int(heightB))
        
        dst = np.array([
                [0, 0],
                [maxWidth - 1, 0],
                [maxWidth - 1, maxHeight - 1],
                [0, maxHeight - 1]], dtype = "float32")
        
        #se corrige y extrae la pantalla, usando como input los puntos y distancias entre ellos
        M = cv2.getPerspectiveTransform(rect, dst)
        warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))
        return [warped,[rect,dst,maxWidth,maxHeight]]
    else:
        rect=pos[0]
        dst=pos[1]
        maxWidth=pos[2]
        maxHeight=pos[3]
        M = cv2.getPerspectiveTransform(rect, dst)
        warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))
        return [warped,[rect,dst,maxWidth,maxHeight]]
        
    

def camera_init(): #inizialización y captura de imagen

    camera = PiCamera()
    camera.resolution = (1920,1080)

    return camera
        
#def data (img):
def camera_take(camera):
    stram = io.BytesIO()
    camera.capture(stram, format = "jpeg")
    data = np.fromstring(stram.getvalue(), dtype=np.uint8)
    img = cv2.imdecode(data,1)
    return img
    
def camera_take2(camera):
    
    rawCapture = PiRGBArray(camera, size=(1920,1080))
    camera.capture(rawCapture, format="bgr")
    image = rawCapture.array
    return image

def camera_take3():
    stream = io.BytesIO()
    with picamera.PiCamera() as camera:
        camera.capture(stream, format='jpeg')
        # Construct a numpy array from the stream
        data = np.fromstring(stream.getvalue(), dtype=np.uint8)
        # "Decode" the image from the array, preserving colour
        image = cv2.imdecode(data, 1)
        # OpenCV returns an array with data in BGR order. If you want RGB instead
        # use the following...
        image = image[:, :, ::-1]
    return image
    
def recorte_2(camera,gamma):
    stream = io.BytesIO()
    camera.capture(stream, format = "jpeg")
    data = np.fromstring(stream.getvalue(), dtype=np.uint8)
    img = cv2.imdecode(data,1)
    
    img=cv2.resize(img,(1000,1200)) 
    
    im_gamma =select(img,gamma)
    gris = cv2.cvtColor(im_gamma, cv2.COLOR_BGR2GRAY)
    gauss = cv2.GaussianBlur(gris, (5,5), 0)
    ret,th = cv2.threshold(gauss,0,255,cv2.THRESH_BINARY)
    cnts = cv2.findContours(th, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    cnts = sorted(cnts, key = cv2.contourArea, reverse = True)[:1]

    rect = np.zeros((4, 2), dtype = "float32")# array donde guardare las esquinas de la pantalla
    for c in cnts:
        approx = cv2.approxPolyDP(c, 0.009 * cv2.arcLength(c, True), True)
        n = approx.ravel()

    pts=np.zeros((int(len(n)/2),2),dtype="float32")

    for k in range (0, int((len(n)/2))): #extraigo los posibles candidatos a esquinas
        pts[k]=[n[2*k],n[2*k+1]]
        
    s= pts.sum(axis = 1)             #A partir de relaciones de maximos y minimas distancias se extraen las 4 esquinas
    rect[0] = pts[np.argmin(s)]
    rect[0][0]=rect[0][0]-5
    rect[2] = pts[np.argmax(s)]
    rect[2][0]=rect[2][0]+4

    diff = np.diff(pts, axis = 1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    rect[3][0]=rect[3][0]-5
    rect[3][0]=rect[3][0]+4

    #(tl, tr, br, bl) = rect #camara derecha
    (bl, br, tr, tl) = rect #camara inv
    #Se definen las distancias entre los puntos
    widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    maxWidth = max(int(widthA), int(widthB))
    heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    maxHeight = max(int(heightA), int(heightB))
    
    dst = np.array([
            [0, 0],
            [maxWidth - 1, 0],
            [maxWidth - 1, maxHeight - 1],
            [0, maxHeight - 1]], dtype = "float32")
    
    #se corrige y extrae la pantalla, usando como input los puntos y distancias entre ellos
    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(img, M, (maxWidth, maxHeight))
    return warped
    
    
    
    
