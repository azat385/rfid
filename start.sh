#!/bin/sh
# start.sh
# navigate to home directory, then to this directory, then execute python script, then back home

sleep 10s
cd /
cd home/pi/rfid
sudo python listenPort.py
cd /

