#!/bin/zsh

# Not needed if Docker used instead

mount /nfs/miniprojects 2>/dev/null

#set -e
rsync --delete -a /nfs/miniprojects/where-u-at/ /root/where-u-at

#if ( ! grep -q 'TIME=0$' /etc/kbd/config ); then
#	sed -i 's/TIME=[0-9]+$/TIME=0/' /etc/kbd/config
#	systemctl restart kbd
#fi

cd /root/where-u-at/ical_to_mqtt

python3 ./ical_to_mqtt.py


