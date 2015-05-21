#!/usr/bin/env python
# -*- coding: utf-8 -*-

import threading
from time import sleep
from datetime import datetime

value = []
value.append("qwert1")
value.append("qwert2")
value.append("qwert3")

def printl():
	global value
	global t
	while len(value):
		print datetime.now(), value.pop(0), value, len(value), threading.currentThread().getName()
		sleep(0.1)
	t = threading.Timer(2, printl, ) 
	t.start()
	for i in xrange(4):
		value.append('qwert'+str(i))
	print value

t = threading.Thread(target = printl)
t.start()
t.join()
