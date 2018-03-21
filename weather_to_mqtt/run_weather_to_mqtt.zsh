#!/bin/zsh

# Not needed if Docker used instead

mount /nfs/miniprojects 2>/dev/null

#set -e
rsync --delete -a /nfs/miniprojects/where-u-at/ /root/where-u-at

cd /root/where-u-at/weather_to_mqtt

python3 ./weather_to_mqtt.py
