#!/bin/zsh

# Copies to local disk to avoid NFS problems

mount /nfs/miniprojects 2>/dev/null

#set -e
rsync --delete -a --exclude .\* --exclude junk /nfs/miniprojects/where-u-at/ /root/where-u-at

#if ( ! grep -q 'TIME=0$' /etc/kbd/config ); then
#	sed -i 's/TIME=[0-9]+$/TIME=0/' /etc/kbd/config
#	systemctl restart kbd
#fi

cd /root/where-u-at/epaperframe

python3 ./epaperframe.py


