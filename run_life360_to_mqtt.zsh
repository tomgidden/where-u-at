#!/bin/zsh

mount /nfs/miniprojects 2>/dev/null

#set -e
rsync --delete -a /nfs/miniprojects/where-u-at/ /root/where-u-at

cd /root/where-u-at

python3 ./life360_to_mqtt.py
