#!/usr/bin/env python
# -*- coding: utf-8 -*-

import serial
from datetime import datetime
from time import sleep
import re
import RPi.GPIO as GPIO
import MySQLdb
import pymssql
import threading
from random import randint,choice	# for testing

from pymodbus.client.sync import ModbusTcpClient as ModbusClient

import logging
from logging.handlers import TimedRotatingFileHandler

logHandler = TimedRotatingFileHandler("logs/logfile", when="midnight") #when = "M")
logHandler.suffix = "%Y-%m-%d.html"
logFormatter = logging.Formatter('%(levelname)-10.10s %(asctime)s [%(funcName)-12.12s] [%(threadName)-15.15s] %(message)s </br>\r')
logHandler.setFormatter( logFormatter )
logger = logging.getLogger( 'MyLogger' )
logger.addHandler( logHandler )
logger.setLevel( logging.INFO ) # CHANGE to INFO after start up!!!
#for console logging
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
logger.addHandler( consoleHandler )

logger.debug('debug message')
logger.info('info message')
logger.warn('warn message')
logger.error('error message')
logger.critical('critical message')

logger.info('PROGRAMM IS STARTING...\n\n')

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
# colors to light up the GPIO above
blue 	= 0b00
green 	= 0b01
red 	= 0b10
yellow	= 0b11

defaultLevel = 2
zeroLevel = 0
clearTimeout = 7.0

# connect buzzer
GPIO3 = 22
GPIO4 = 23

class sql():
	def __init__(self, host, user, pswd, db, type):
		self.host = host
		self.user = user
		self.pswd = pswd
		self.db   = db
		self.type = type
	def connection(self):
		return (self.host, self.user, self.pswd, self.db)

# connection *args
localSQL = sql('localhost', 'script', '1qaz2wsx', 'rfid', 'MySQL')
remoteSQL = sql('192.168.57.253\SQLSERVER2005', 'bolid', 'bolid', 'Orion', 'MS SQL')
# use *sql.connection() to pass *args

class RepeatedAction(object):
    def __init__(self, interval, function, *args, **kwargs):
        self._timer     = None
        self.interval   = interval
        self.function   = function
        self.args       = args
        self.kwargs     = kwargs
        self.isRunning = False
        self.start()

    def _run(self):
        self.isRunning = False
        self.start()
        self.function(*self.args, **self.kwargs)

    def start(self):
        if not self.isRunning:
            self._timer = threading.Timer(self.interval, self._run)
            self._timer.start()
            self.isRunning = True

    def stop(self):
        self._timer.cancel()
        self.isRunning = False


def setupGPIO():
    GPIO.setmode(GPIO.BCM)
    GPIO.cleanup()
    GPIO.setup(GPIO1, GPIO.OUT)
    GPIO.setup(GPIO2, GPIO.OUT)

def writeColor(_color):
    GPIO.output(GPIO1, int(1&_color >0))
    GPIO.output(GPIO2, int(2&_color >0))

def setColor(_color, _timeout = clearTimeout):
    global writeInitColor
    writeColor(_color)
    if writeInitColor.isAlive():
	 writeInitColor.cancel()
    writeInitColor = threading.Timer(_timeout,writeColor,[blue,])
    writeInitColor.start()

def setRelay(_level):
    #"{:08b}".format(127)
    i = 0
    for relay in GPIORelay:
 	GPIO.output(relay, int((_level>>i) & 1) )
	#print relay, (_level>>i) & 1, type (int ((_level>>i) & 1))
	i+=1

def setWAGO(_level):
    global setToInit
    if writeWAGO(_level):
	if setToInit.isAlive():
            setToInit.cancel()
        setToInit = threading.Timer(clearTimeout,writeWAGO,[zeroLevel,])
        setToInit.start()


def writeWAGO(_level):
    DO = [((_level >> i) & 1)==1 for i in range(8)]
    #master.execute(1, cst.READ_COILS, 512, 8)
    #master.execute(1, cst.WRITE_MULTIPLE_COILS, 512, output_value=[1, 1, 0, 1, 1, 0, 1, 1])
    if client.connect():
    	rw = client.write_coils(0x200,DO,unit=1)
    	DO_readback = client.read_coils(0x200,8,unit=1).bits
	client.close()
	if checkEquality(DO,DO_readback):
            logger.debug('write is OK')
	    return 1
	else:
	    logger.error("write!=read")
	    return 0
    else:
	threading.Thread(target=setColor, args=(yellow,3,)).start()
        logger.error('NO connection')
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

def readSQL():
    global dictCodeToLevel
    updateSQL()
    db = MySQLdb.connect(*localSQL.connection())
    curs=db.cursor()

    if curs.execute ("SELECT code,level FROM elevator"):
	logger.debug("updating the dict from SQL")
	for d in curs.fetchall():
	    dictCodeToLevel[d[0]]=d[1]	    
    else:
	logger.error("NO connection to local SQL db")
	pass # error logging
    db.close()

def updateSQL():
    """update local mySQL from MS SQL """
    pass

def writeSQL():
    global arrWriteToSQL
    if len(arrWriteToSQL):
	pass
	logger.debug("Starting...")
    else:
	logger.debug("Nothing to write to SQL exiting sub")
	return
    con = pymssql.connect(*remoteSQL.connection())
    cur = con.cursor()
    
    logger.debug("arrWriteToSQL = '{}' to be commited".format(str(arrWriteToSQL)))
    while len(arrWriteToSQL):
	write = arrWriteToSQL.pop(0)
	cur.execute("EXEC dbo.test_ins '{}', '{}'".format(write[0], write[1]) )
    logger.debug("Commit MS SQL db")
    con.commit()
    con.close()
    logger.debug("Ending...")

def getRandomCode():
    global dictCodeToLevel
    return choice(dictCodeToLevel.keys())

#if __name__ == '__main__': 

# initate global variables
dictCodeToLevel = {}
arrWriteToSQL 	= []

# setup UART port
ser = serial.Serial(port='/dev/ttyAMA0', baudrate=2400, bytesize=8, 
		    parity='N', stopbits=1, timeout=0.1, 
		    xonxoff=0, rtscts=0)
# GPIO
setupGPIO()

# connectWAGO
client = ModbusClient(host = '192.168.55.9', port = 502, timeout = 1)

# inital Threads
setToInit = threading.Timer(1.0,setWAGO,[zeroLevel,])
setToInit.start()

writeInitColor = threading.Timer(1.0,writeColor,[blue,])
writeInitColor.start()

# start repeated Actions
writeSQL()
wSQL = RepeatedAction(60, writeSQL,)	# runs evety 5 min
readSQL()
rSQL = RepeatedAction(60, readSQL,)	# runs every 1 hour

hexString = lambda byteString : " ".join(x.encode('hex') for x in byteString)

while True:
	response = ser.read(size=100)
	#sleep(randint(10,20))
	#if True:
	if response:
		bolidCode =  wiegandToTM("00 38 85 9D 68 48 ")
		#bolidCode =  getRandomCode()
		bolidCode =  wiegandToTM(hexString(response))

		if bolidCode in dictCodeToLevel:
			level = dictCodeToLevel[bolidCode]
		else:
			level = -1

		if level <= 0:
			logger.warn("READ:'{}' BOLID:'{}' LEVEL'{}'\t= {:08b}".format(hexString(response), bolidCode, level, level))
			level = defaultLevel
			currentColor = red
		elif level > 0:
			logger.info("READ:'{}' BOLID:'{}' LEVEL'{}'\t= {:08b}".format(hexString(response), bolidCode, level, level))
			currentColor = green
		
		setWAGOThread = threading.Thread(target=setWAGO, args=(level,))
		setWAGOThread.start()
		
		setColorThread = threading.Thread(target=setColor, args=(currentColor,))
		setColorThread.start()
		
		# add to array --> write to MS SQL later
		arrWriteToSQL.append( [bolidCode, str(datetime.now())[:-3] ] )
