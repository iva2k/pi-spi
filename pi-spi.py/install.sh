#!/bin/bash

CONFIG=/boot/config.txt

is_pi () {
  ARCH=$(dpkg --print-architecture)
  if [ "$ARCH" = "armhf" ] ; then
    return 0
  else
    return 1
  fi
}

if is_pi ; then
  CMDLINE=/boot/cmdline.txt
else
  CMDLINE=/proc/cmdline
fi

# Must be on pi
if ! is_pi ; then
  printf "Only Raspberry Pi is supported.\n"
  exit 1
fi

# Must be root
if [ $(id -u) -ne 0 ]; then
  printf "Must be root. Did you use 'sudo'?\n"
  exit 1
fi

printf "\nInstalling packages...\n"
sudo apt-get update
sudo apt-get install -y python-dev python-spidev
sudo apt-get install -y python3-dev python3-spidev
sudo apt-get install -y python-rpi.gpio python3-rpi.gpio
sudo apt-get install -y samba samba-common-bin

printf "\nInstalling files...\n"
sudo cp -rv pkg/* /

# TODO: copy pkg/home/pi/* files to appropriate home directory. How can we know what user is to be run under?
#shopt -s dotglob ;# bash will not find hidden .xxx files and complain, fix it with dotglob
#sudo cp -rv pkg/home/pi/* ~/
#shopt -u dotglob ;# restore

printf "\nEnabling services...\n"
sudo systemctl daemon-reload
#sudo systemctl start webcam-video.service
#sudo systemctl enable webcam-video.service
#sudo systemctl enable splashscreen.service

printf "Adjusting settings...\n"
echo 0 | sudo tee /sys/class/graphics/fb0/blank >/dev/null
sudo cp $CMDLINE $CMDLINE.bak
sed -i $CMDLINE -e "s/ quiet//"
sed -i $CMDLINE -e "s/ splash//"
sed -i $CMDLINE -e "s/ plymouth.ignore-serial-consoles//"
sed -i $CMDLINE -e "s/ plymouth.enable=[0-1]//"
sed -i $CMDLINE -e "s/ loglevel=[0-9]//"
sed -i $CMDLINE -e "s/ logo.nologo//"
sed -i $CMDLINE -e "s/ vt.global_cursor_default=[0-1]//"
sed -i $CMDLINE -e "s/$/ quiet splash plymouth.ignore-serial-consoles/"
sed -i $CMDLINE -e "s/$/ plymouth.enable=0 loglevel=3 logo.nologo vt.global_cursor_default=0/"

printf "\nDone.\n"
