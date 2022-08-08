#!/bin/bash

webcam=/dev/video0
fb=/dev/fb0
width=1600
height=1200
rate=5/1
mrate=30/1
format=YUY2

# Show an overlay
overlay=
#overlay="clockoverlay time-format=\"%Y/%m/%d %H:%M:%S\" ! "

# Measure FPS:
fps=
# fps=fpsdisplaysink video-sink=

for i in "$@"
do
case $i in
  -d=*|--device=*)
    webcam="${i#*=}"
    shift # past argument=value
    ;;
  -o=*|--output=*)
    fb="${i#*=}"
    shift # past argument=value
    ;;
  -w=*|--width=*)
    width="${i#*=}"
    shift # past argument=value
    ;;
  -h=*|--height=*)
    height="${i#*=}"
    shift # past argument=value
    ;;
  -r=*|--rate=*)
    rate="${i#*=}"
    shift # past argument=value
    ;;
  -f=*|--format=*)
    format="${i#*=}"
    shift # past argument=value
    ;;
  --clock)
    overlay="clockoverlay time-format=\"%Y/%m/%d %H:%M:%S\" ! "
    ;;
  *)
    printf "Unknown option '$i'.\n"
    printf "Usage: $0 [options].\n"
    exit 1
    ;;
esac
done

# raw video format, ~5fps
gst-launch-1.0 -v v4l2src device=$webcam ! video/x-raw,width=$width,height=$height, framerate=$rate, format=$format ! $overlay videoconvert ! ${fps}fbdevsink device=$fb sync=false

# mjpeg format, no GPU, ~2.7fps
# gst-launch-1.0 -v v4l2src device=$webcam ! image/jpeg,width=$width,height=$height, framerate=$mrate ! jpegparse ! jpegdec ! $overlay videoconvert ! ${fps}fbdevsink device=$fb sync=false

# mjpeg format, with GPU / needs omx, ~3.5fps
# gst-launch-1.0 -v v4l2src device=$webcam ! image/jpeg,width=$width,height=$height, framerate=$mrate ! omxmjpegdec ! $overlay videoconvert ! ${fps}fbdevsink device=$fb sync=false

#black screen: gst-launch-1.0 -v v4l2src device=/dev/video0 ! image/jpeg,width=1600,height=1200, framerate=30/1 ! jpegparse ! omxmjpegdec ! $overlay videoconvert ! ${fps}fbdevsink device=/dev/fb0
#works       : gst-launch-1.0 -v v4l2src device=/dev/video0 ! image/jpeg,width=1600,height=1200, framerate=30/1 !             omxmjpegdec ! $overlay videoconvert ! ${fps}fbdevsink device=/dev/fb0
#errors      : gst-launch-1.0 -v v4l2src device=/dev/video0 ! image/jpeg,width=1600,height=1200, framerate=30/1 !             omxmjpegdec                         ! ${fps}fbdevsink device=/dev/fb0

