from gpiozero import LED
from time import sleep

def leds(estado,a):
    if a==1:
        estado[0].on()
        estado[1].off()
        estado[2].off()
    elif a==2:
        estado[0].off()
        estado[1].on()
        estado[2].off()
    elif  a==3:
        estado[0].off()
        estado[1].off()
        estado[2].on()
    elif  a==4:
        estado[0].on()
        estado[1].on()
        estado[2].on()
    else:
        estado[0].off()
        estado[1].off()
        estado[2].off()
        
