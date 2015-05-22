class sql():
	def __init__(self, host, user, pswd, db, type):
		self.host = host
		self.user = user
		self.pswd = pswd
		self.db   = db
		self.type = type
	def connection(self):
		return (self.host, self.user, self.pswd, self.db)


localSQL = sql('localhost', 'script', '1qaz2wsx', 'rfid', 'MySQL')
remoteSQL = sql('192.168.57.253\SQLSERVER2005', 'bolid', 'bolid', 'Orion', 'MS SQL')


import MySQLdb
db = MySQLdb.connect(*localSQL.connection())
curs=db.cursor()

import pymssql

con = pymssql.connect(*remoteSQL.connection())
cur = con.cursor()








import logging
from logging.handlers import TimedRotatingFileHandler

logHandler = TimedRotatingFileHandler('logs/logfile', when='midnight') #when = 'M')
logHandler.suffix = '%Y-%m-%d_%H-%M.html'
logFormatter = logging.Formatter('%(levelname)-10.10s %(asctime)s [%(funcName)-12.12s] [%(threadName)-15.15s] %(message)s </br>\r')
logHandler.setFormatter( logFormatter )
logger = logging.getLogger( 'MyLogger' )
logger.addHandler( logHandler )
logger.setLevel( logging.DEBUG )#INFO
#for console logging
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
logger.addHandler( consoleHandler )

logger.debug('This message should go to the log file')
logger.info('So should this')
logger.warning('And this, too')

logger.debug('debug message')
logger.info('info message')
logger.warn('warn message')
logger.error('error message')
logger.critical('critical message')

logging.basicConfig(
filename='exampleLog.html',
format='%(levelname)s\t%(asctime)s %(message)s</br>\r',
level=logging.DEBUG)

#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pymssql

con = pymssql.connect(host='192.168.57.253\SQLSERVER2005', user='bolid', password='bolid', database='Orion')

cur = con.cursor()

cur.execute('SELECT TOP 20 CodeP, OwnerName FROM pMark WHERE id >100')
cur.execute('SELECT CodeP, OwnerName FROM pMark')
data = cur.fetchall()

18 Ширшова
15 Мишинкин


cur.callproc('test_sel', (30,))
cur.execute('SELECT dbo.test_sel(30)')
result = cur.fetchall()
print result[0][0]

cur.execute('EXEC dbo.test_ins 'timeNow', '{}''.format(str(datetime.now())[:-3]) )
con.commit()
con.close()
SELECT * FROM test_f;







for i in data[12][0].encode('cp1251')[::-1]: print 'byte = '{}'\t dec = '{}'\t hex = '{}''.format(i, ord(i), hex(ord(i)));
hexString = lambda byteString : ' '.join(x.encode('hex') for x in byteString.encode('cp1251')[1:6][::-1])
wiegandToTM(hexString(data[12][0]))

def getWiegandFromSQL(byteString, debug = 0):
	wiegand = []
	byteString = byteString.encode('cp1251')[1:]
	ibyteString = iter(byteString)
	for x in ibyteString:
		b = x.encode('hex')
		if  b =='fe':
			if ibyteString.next().encode('hex') == '01':
				if debug: print '00';
				wiegand.append('00')
				continue
			else:
				pass
				if debug: print 'Continue here'
		else:
			if debug: print b
			wiegand.append(b)
		if debug: print
	result = ' '.join(wiegand[::-1])
	return result, len(wiegand)

getWiegandFromSQL(data[12][0])
	
for i in cur.fetchall():
   i=unicode(i[0],'windows-1251')
   print '%s' % i.encode('utf-8')

con.commit()
con.close()



