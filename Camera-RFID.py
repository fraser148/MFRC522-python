#!/usr/bin/env python
# -*- coding: utf8 -*-

import RPi.GPIO as GPIO
import MFRC522
import signal
import time
import os
import commands

GPIO.setwarnings(False)

GPIO.setmode(GPIO.BOARD)

#Set up variables and initialise
counter = 0
LED_ON = 3
LED_OFF = 8
BTN_GO = 5
OF = 1
pid = 0
loop = 1

continue_reading = True

OUT = (LED_ON, LED_OFF)
IN = (BTN_GO)

for i in OUT:
    GPIO.setup(i,GPIO.OUT)

for i in OUT:
    GPIO.output(i,0)

GPIO.setup(BTN_GO, GPIO.IN, pull_up_down=GPIO.PUD_UP)

GPIO.output(LED_OFF, 1)


MIFAREReader = MFRC522.MFRC522()

def end_read(signal,frame):
    global continue_reading
    print "Ctrl+C captured, ending read."
    continue_reading = False
    GPIO.cleanup()


def scan():
    while continue_reading:
          
        (status,TagType) = MIFAREReader.MFRC522_Request(MIFAREReader.PICC_REQIDL)

        # If a card is found
        #if status == MIFAREReader.MI_OK:
         #   print "Card detected"
        
        (status,uid) = MIFAREReader.MFRC522_Anticoll()

        if status == MIFAREReader.MI_OK:

            # Print UID
            #print "Card read UID: "+str(uid[0])+","+str(uid[1])+","+str(uid[2])+","+str(uid[3])
        
            key = [0xFF,0xFF,0xFF,0xFF,0xFF,0xFF]
            
            MIFAREReader.MFRC522_SelectTag(uid)

            status = MIFAREReader.MFRC522_Auth(MIFAREReader.PICC_AUTHENT1A, 8, key, uid)
            print "\n"

            if status == MIFAREReader.MI_OK:
                MIFAREReader.MFRC522_Read(8)
                MIFAREReader.MFRC522_StopCrypto1()
				
                #Here the 'data' variable is what you change. If the right card has the right data (equal to this) then it will be allowed
                data = "39,90,44,60"
                print(data)
                
                #Read the UID from the card
                datauth = str(uid[0])+","+str(uid[1])+","+str(uid[2])+","+str(uid[3])
                print(datauth)
				
                #If the card's UID is equal to the 'data' variable then the camera will turn on.
                if datauth == data:
                    #If the variable showing whether the camera is on or off is equal to 1, this means that the camera is off
                    #so it will go through the turning on sequence.
                    if OF == 1:
                        GPIO.output(LED_OFF, 0)
                        #The off LED will blink and then the on LED will come on
                        for x in range (0,4):
                            GPIO.output(LED_OFF,1)
                            time.sleep(0.5)
                            GPIO.output(LED_OFF,0)
                            time.sleep(0.5)
                        GPIO.output(LED_ON, 1)
                        #The is switched on
                        os.system("mkdir /tmp/stream")
                        os.system("raspistill --nopreview -w 640 -h 480 -q 5 -o /tmp/stream/pic.jpg -tl 100 -t 9999999 -th 0:0:0 &")
                        os.system('LD_LIBRARY_PATH=/usr/local/lib mjpg_streamer -i "input_file.so -f /tmp/stream -n pic.jpg " -o "output_http.so -w /usr/local/www " &')
                        #The variable here is to show that the camera is on (OF = 0)
                        global OF
                        OF = 0
                        return OF
                    #If the camera is already on (ie OF = 0) then the sequence for turning off the camera will run:
                    else:
                        GPIO.output(LED_ON, 0)
                        GPIO.output(LED_OFF, 1)
                        #This small section of code was extremely hard to get but it searches for the most recent command involving "raspistill" ie turning the camera on
                        #And then gets it process id (pid). The first 4 numbers of the pid are taken as this is the most recent process and then the process is killed,
                        #switching off the camera.
                        pid = commands.getoutput("pgrep -f raspistill")
                        pid = pid[:4]
                        print(pid)
                        os.system("sudo kill " + pid)
                        global OF
                        OF = 1
                        return OF
                        time.sleep(2)
                 #If the card is not the correct card, the off LED will blink showing that it is the wrong card
                else:
                    for x in range (0,5):
                            GPIO.output(LED_OFF,1)
                            time.sleep(0.1)
                            GPIO.output(LED_OFF,0)
                            time.sleep(0.1)
                    if OF == 1:
                        GPIO.output(LED_ON,0)
                        GPIO.output(LED_OFF,1)
                    else:
                        GPIO.output(LED_ON,1)
                        GPIO.output(LED_OFF,0)
                        
                    print("Unauthorised")
                    

            
            else:
                print "Authentication error"


signal.signal(signal.SIGINT, end_read)

while True:
    scan()