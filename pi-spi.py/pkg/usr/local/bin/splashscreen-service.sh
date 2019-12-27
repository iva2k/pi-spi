#!/bin/bash

# based on https://raspberry-projects.com/pi/pi-operating-systems/raspbian/custom-boot-up-screen

### BEGIN INIT INFO
# Provides:          splashscreen
# Required-Start:
# Required-Stop:
# Should-Start:
# Default-Start:
# Default-Stop:
# Short-Description: Show custom splashscreen
# Description:       Show custom splashscreen
### END INIT INFO

audio_delay=3 ;# seconds
duration=10   ;# seconds
blend=3000    ;# milliseconds

do_start () {
  if [ -f /etc/boot.jpg ]; then
    sudo /usr/bin/fbi -T 1 -t $duration --once --noverbose --blend $blend /etc/boot.jpg > /dev/null 2>&1 &
  fi
  if [ -f /etc/boot.wav ]; then
    /bin/sleep $audio_delay
    sudo /usr/bin/aplay /etc/boot.wav >/dev/null 2>&1 &
  fi
  if [ -f /home/pi/app_info ]; then
    type=`cat /home/pi/app_info | grep Type | cut -d ' ' -f 2`
    if [ -f /home/pi/$type/manager.py ]; then
      sudo /bin/openvt  -c 1 -f -- /usr/bin/python /home/pi/$type/manager.py --vt 2
    else
      echo "error: file /home/pi/$type/manager.py not found"
    fi
  fi
  /bin/sleep $duration
  exit 0
}

case "$1" in
  start|"")
    do_start
    ;;
  restart|reload|force-reload)
    echo "Error: argument '$1' not supported" >&2
    exit 3
    ;;
  stop)
    # No-op
    exit 0
    ;;
  status)
    exit 0
    ;;
  *)
    echo "Usage: $0 [start|stop]" >&2
    exit 3
    ;;
esac
