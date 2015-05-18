#!/usr/bin/env python
# -*- coding: utf-8 -*-

import serial
from datetime import datetime
from time import sleep
import re
import RPi.GPIO as GPIO
import MySQLdb
import threading

from pymodbus.client.sync import ModbusTcpClient as ModbusClient

CRCTable = (
0,94,188,226,97,63,221,131,194,156,126,32,163,253,31,65,
157,195,33,127,252,162,64,30,95,1,227,189,62,96,130,220,
35,125,159,193,66,28,254,160,225,191,93,3,128,222,60,98,
190,224,2,92,223,129,99,61,124,34,192,158,29,67,161,255,
70,24,250,164,39,121,155,197,132,218,56,102,229,187,89,7,
219,133,103,57,186,228,6,88,25,71,165,251,120,38,196,154,
101,59,217,135,4,90,184,230,167,249,27,69,198,152,122,36,
248,166,68,26,153,199,37,123,58,100,134,216,91,5,231,185,
140,210,48,110,237,179,81,15,78,16,242,172,47,113,147,205,
17,79,173,243,112,46,204,146,211,141,111,49,178,236,14,80,
175,241,19,77,206,144,114,44,109,51,209,143,12,82,176,238,
50,108,142,208,83,13,239,177,240,174,76,18,145,207,45,115,
202,148,118,40,171,245,23,73,8,86,180,234,105,55,213,139,
87,9,235,181,54,104,138,212,149,203,41,119,244,170,72,22,
233,183,85,11,136,214,52,106,43,117,151,201,74,20,246,168,
116,42,200,150,21,75,169,247,182,232,10,84,215,137,107,53)

GPIO1 = 17 # BCM counting
GPIO2 = 18
defaultColor = 'blue'
colorToGPIO = {'blue':0, 'green':1, 'red':2, 'yellow':3}
GPIORelay = [5, 6, 13, 19, 26, 16, 20, 21]
defaultLevel = 2
zeroLevel = 0

def setupGPIO():
    GPIO.setmode(GPIO.BCM)
    GPIO.cleanup()
    GPIO.setup(GPIO1, GPIO.OUT)
    GPIO.setup(GPIO2, GPIO.OUT)
    for relay in GPIORelay:
	 GPIO.setup(relay, GPIO.OUT)

def setGPIO(color):
    GPIO.output(GPIO1, 1&color)
    GPIO.output(GPIO2, 2&color)

def setRelay(_level):
    #"{:08b}".format(127)
    i = 0
    for relay in GPIORelay:
 	GPIO.output(relay, int((_level>>i) & 1) )
	#print relay, (_level>>i) & 1, type (int ((_level>>i) & 1))
	i+=1
def setWAGO(_level):
    DO = [((_level >> i) & 1)==1 for i in range(8)]
    #master.execute(1, cst.READ_COILS, 512, 8)
    #master.execute(1, cst.WRITE_MULTIPLE_COILS, 512, output_value=[1, 1, 0, 1, 1, 0, 1, 1])
    if client.connect():
    	rw = client.write_coils(0x200,DO,unit=1)
    	DO_readback = client.read_coils(0x200,8,unit=1).bits
	client.close()
	if checkEquality(DO,DO_readback):
            print "OK"
	    return 1
	else:
	    print "write!=read"
	    return 0
    else:
        print "NO connection"
	return 0

def checkEquality(arr1, arr2):
    if len(arr1)!=len(arr2):
	return False
    result = True
    for a1,a2 in zip(arr1, arr2):
	if a1!=a2:
	    return False
    return result

def wiegandToTM( wiegand):
    #wiegand = "00 38 85 9D 68 48 "
    wiegand = wiegand.replace(' ', '')
    wiegand = wiegand[:-2]+'01'
    wiegand = wiegand.zfill(14)
    code = re.findall("..?", wiegand)
    #[wiegand[i:i+n] for i in range(0, len(wiegand), 2)]
    code = [int(i,16) for i in code]
    code = code[::-1]
    CRC = 0
    for i in code:
        CRC = CRCTable[CRC ^ i]
    code.append(CRC)
    return "".join("%0.2X"%i for i in code[::-1])

def connectSQL():
    db = MySQLdb.connect("localhost", "script", "1qaz2wsx", "rfid")
    curs=db.cursor()

def readSQL(code):
    if  curs.execute ("SELECT `level` FROM elevator WHERE code = '{}'".format(code)):
	return curs.fetchall()[0][0]
    else:
	return -1

def writeSQL(code):
    curs.execute ("INSERT INTO `rfid`.`passed` (`code`) VALUES ('{}')".format(code))
    db.commit()

#if __name__ == '__main__': 

ser = serial.Serial(port='/dev/ttyAMA0', 
baudrate=2400, 
bytesize=8, 
parity='N', 
stopbits=1, 
timeout=0.1, 
xonxoff=0, 
rtscts=0)

setupGPIO()
#connectSQL()
db = MySQLdb.connect("localhost", "script", "1qaz2wsx", "rfid")
curs=db.cursor()

#connectWAGO
client = ModbusClient(host = '192.168.55.9', port = 502, timeout = 1)

setToInit = threading.Timer(3.0,setWAGO,[zeroLevel,])
setToInit.start()

hexString = lambda byteString : " ".join(x.encode('hex') for x in byteString)
while True:
	response = ser.read(size=100)
	if response:
		#print response
		bolidCode =  wiegandToTM(hexString(response))
		level = readSQL(bolidCode)
		
		print "{} READ:'{}' BOLID:'{}' LEVEL'{}'\t= {:08b}".format(datetime.now(), hexString(response), bolidCode, level, level)
		if level < 0:
			level = defaultLevel
			setGPIO(colorToGPIO['red'])
		elif level == 0:
			level = defaultLevel
			setGPIO(colorToGPIO['yellow'])
		elif level > 0:
			#setWAGO(level)
			setGPIO(colorToGPIO['green'])
		setWAGO(level)
		if setToInit.isAlive():
			setToInit.cancel()
		setToInit = threading.Timer(3.0,setWAGO,[zeroLevel,])
		setToInit.start()
		sleep(0.3)
		writeSQL(bolidCode)
		#curs.execute ("""INSERT INTO `rfid`.`passed` (`code`) VALUES ('{}')""".format(bolidCode))
		#db.commit()
	setGPIO(colorToGPIO['blue'])
