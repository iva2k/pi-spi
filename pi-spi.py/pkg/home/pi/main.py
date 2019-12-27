#!/usr/bin/python
from __future__ import print_function

# Define GPIO pins and interfaces to use
SPI_VCC = 22
SPI_WP = 5
SPI_HOLD = 6
SPI = 0
#SPI = 1
CS = 0
#CS = 1

from spiflash import spiflash

try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
except:
    print("RPi.GPIO: incompatible platform, using rpidevmocks.MockGPIO")
    from rpidevmocks import MockGPIO
    GPIO = MockGPIO()


#import gpiozero

#helpers -------------------------------------------------------------------------------
def print_status(status):
    print("status %s %s" % (bin(status[1])[2:].zfill(8), bin(status[0])[2:].zfill(8)))

def print_page(page):
    s = ""
    for row in range(16):
        for col in range(15):
            s += "%02X " % page[row * 16 + col]
        s += "\n"
    print(s) 

def ReverseBits(byte):
    byte = ((byte & 0xF0) >> 4) | ((byte & 0x0F) << 4)
    byte = ((byte & 0xCC) >> 2) | ((byte & 0x33) << 2)
    byte = ((byte & 0xAA) >> 1) | ((byte & 0x55) << 1)
    return byte
#end def

def BytesToHex(Bytes):
    return ''.join(["0x%02X " % x for x in Bytes]).strip()
#end def

# Setup GPI, Open chip
GPIO.setup(SPI_VCC, GPIO.OUT, initial=GPIO.HIGH)
GPIO.output(SPI_VCC, GPIO.HIGH)
GPIO.setup(SPI_WP, GPIO.OUT, initial=GPIO.HIGH)
GPIO.output(SPI_WP, GPIO.HIGH)
GPIO.setup(SPI_HOLD, GPIO.OUT)
GPIO.output(SPI_HOLD, GPIO.HIGH)
chip = spiflash(bus = SPI, cs = CS)

#TESTS -------------------------------------------------------------------

print("read JEDEC ID...")
print(chip.read_jedec_id())

#print_status(read_status())
#write_disable()
#print_status(read_status())

print("checking busy...")
chip.wait_until_not_busy()
print("reading page...")
p = chip.read_page(0, 0)
print_page(p)

#print "erasing chip"
#chip.erase_all()
#print "chip erased"

# for i in range(256):
#     p[i] = (i + 2) % 256
# print_page(p)
# chip.write_status(0,0)
# print_status(chip.read_status())
# print chip.write_and_verify_page(0,0,p)
# ## Verify:
# chip.print_page(chip.read_page(0,0))

#chip.wait_until_not_busy()
#print_status(chip.read_status())
#write_status(0,0)
#print_status(chip.read_status())
