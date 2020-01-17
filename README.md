# pi-spi

This project makes Raspberry Pi into a SPI EEPROM/Flash programmer, e.g. for using it with PC motherboards to fiddle with their CMOS memory.

Either clone Github repo <https://github.com/iva2k/pi-spi> directly to Pi or upload all files to it over SCP/SSH from Windows (if Git is installed on Windows, it has scp implementation) using ```upload.cmd```, then SSH to Pi and run ```install.sh``` from one of subfolders:

* pi-spi.py - python based implementation

TODO: TBD: Once installed, corresponding service will load on boot.

TODO: TBD if Quad-SPI is possible (faster I/O)

Connect SPI device (either probe cable or chip socket) as follows:

| Chip Pin | Chip Signal  | Pi Pin | Pi Signal      | Notes       |
|:--------:|:------------:|:------:|----------------|-------------|
|  8       | VCC          | 17     | +3.3V          | or GPIO(*)  |
|  5       | DI (IO0)     | 19     | MOSI / GPIO 10 |             |
|  2       | DO (IO1)     | 21     | MISO / GPIO 9  |             |
|  6       | CLK          | 23     | SCLK / GPIO 11 |             |
|  4       | GND          | 25     | GND            |             |
|  1       | /CS          | 24     | CE0 / GPIO 8   | Default     |
|  1       | /CS          | 26     | CE1 / GPIO 7   | Alternative |
|  3       | /WP (IO2)    | TBD    | +3.3V          | or GPIO(*)  |
|  7       | /HOLD        | TBD    | +3.3V          | or GPIO(*)  |

TODO: Verify mobo chip pinout

TODO: select which CEx to use in the service (/etc/default/??)

## Dev.Notes

* install raspbian lite
* change password
* enable SSH
* optional: connect to WiFi (or use LAN port for networking)
* enable SPI

/dev/spidev0.0 (CE0) and /dev/spidev0.1 (CE1)

sudo raspi-config
Advanced Options > SPI > Yes > Finish

```bash
## spidev
sudo apt-get install python-dev python-spidev python-pip
sudo apt-get install python3-dev python3-spidev python3-pip
#cd ~
#git clone https : //github.com/doceme/py-spidev.git
#cd py-spidev
#make
#sudo make install

## RPi.GPIO
sudo apt-get install python-rpi.gpio python3-rpi.gpio
# sudo pip install RPi.GPIO gpiozero
# sudo pip-3.2 install RPi.GPIO gpiozero
## ## gpiozero (higher-level lib, not really needed)
## sudo apt-get install python-gpiozero python3-gpiozero
## sudo pip install RPi.GPIO gpiozero
## sudo pip-3.2 install RPi.GPIO gpiozero

## Pi Mocks (ONLY needed on platforms other than Pi, e.g. MacOS, Windows - for cross-development)
pip install git+https://github.com/iva2k/raspi-device-mocks.git
# Note, for development, use:
pip install -e git+https://github.com/iva2k/raspi-device-mocks.git#egg=raspi-device-mocks
# ... then can edit source in <env>/src/rpidevmocks/ and commit to github.
# Or, can link source directly from another location:
pip install -e c:/dev/raspi-device-mocks --no-binary :all:
pip install cliff

```

### SAMBA File Sharing

```bash
sudo apt-get install samba samba-common-bin
sudo smbpasswd -a pi

sudo nano /etc/samba/smb.conf

[share]
Comment = pi-spi shared folder
Path = /
Browseable = yes
Writeable = Yes
only guest = no
create mask = 0777
directory mask = 0777
Public = yes
Guest ok = no


sudo /etc/init.d/samba-ad-dc restart
sudo /etc/init.d/smbd restart

```

### SPI Flash ROM

<https://www.flashrom.org/Flashrom>

### spidev

See pkg/home/pi/*.py files.

### SPI ADC Python Code

```python
#!/usr/bin/python
# -*- coding: utf-8 -*-
# SPI_MCP3304.py: read 8-channel ADC, based on http://www.havnemark.dk/?p=54

# mcp3008_lm35.py - read an LM35 on CH0 of an MCP3008 on a Raspberry Pi
# mostly nicked from
#  http://jeremyblythe.blogspot.ca/2012/09/raspberry-pi-hardware- spi-analog-inp$
# Changed to work w. MCP3308 by Kim H. Rasmussen, June 2013
import spidev
import time

spi = spidev.SpiDev()
spi.open(0, 0)

def readadc(adcnum):
    # read SPI data from MCP3008 chip, 8 possible adc's (0 thru 7)
    if adcnum > 7 or adcnum < 0:
        return -1

    # Frame format: 0000 1SCC | C000 000 | 000 000
    r = spi.xfer2([((adcnum & 6) >> 1)+12 , (adcnum & 1) << 7, 0])
    adcout = ((r[1] & 15) << 8) + r[2]

    # Read from ADC channels and convert the bits read into the voltage
    # Divisor changed from 1023 to 4095, due to 4 more bits
    return (adcout * 3.3) / 4095

while True:
    # Read all channels
    for i in range(8):
        print "%.4f" % (readadc(i)),
    print ""

    time.sleep(0.1)

```

```python
#!/usr/bin/python
# nightlight.py - toggle LED on Raspberry Pi GPIO on/off given MCP3304 ADC to OPT101 ambient light reading
# https://medium.com/@rxseger/spi-interfacing-experiments-eeproms-bus-pirate-adc-opt101-with-raspberry-pi-9c819511efea

import spidev
import time
import RPi.GPIO as GPIO

# /dev/spidev(bus).(dev)
SPI_BUS = 0
# CE0 = 0, CE1=1
SPI_DEV = 0
# MCP3304 channel number, 0 to 7
ADC_CHANNEL = 7

# voltages if greater than or less than, recognize as light or dark (in between, no change)
V_LIGHT = 0.7  # turn off when light out
V_DARK = 0.6   # turn on when it is dark

# GPIO port for nightlight
LED_Y = 32 # G12


GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
GPIO.setup([LED_Y], GPIO.OUT, initial=GPIO.HIGH)

spi = spidev.SpiDev()
spi.open(SPI_BUS, SPI_DEV)

# based on http://www.havnemark.dk/?p=54 and http://jeremyblythe.blogspot.ca/2012/09/raspberry-pi-hardware-spi-analog-inp
def readadc(adcnum):
    # read SPI data from MCP3008 chip, 8 possible adc's (0 thru 7)
    if adcnum > 7 or adcnum < 0:
        return -1

    # Frame format: 0000 1SCC | C000 000 | 000 000
    r = spi.xfer2([((adcnum & 6) >> 1)+12 , (adcnum & 1) << 7, 0])
    adcout = ((r[1] & 15) << 8) + r[2]

    # Read from ADC channels and convert the bits read into the voltage
    # Divisor changed from 1023 to 4095, due to 4 more bits
    return (adcout * 3.3) / 4095

def set_light(on):
    GPIO.output(LED_Y, not on) # active-low

while True:
    v = readadc(7)
    #print v
    if v > V_LIGHT:
        set_light(False)
    elif v < V_DARK:
        set_light(True)
    time.sleep(0.1)
```

## System LEDs

<https://raspberrypi.stackexchange.com/questions/70013/raspberry-pi-3-model-b-system-leds>

## Chips Data

### Winbond W25Q64FV

64Mbit
3V (2.7~3.6V) 4mA
100000 erase/program cycles
20yr data retention
4kB sectors
32/64kB blocks
1~256B programming page
SFDP register
/WP with ()CMP, SEC, TB, BP2, BP1 and BP0) bits and SRP bits
/HOLD Z-state on DO pin
CLK rising edge to write DI (MSB first) to chip, master DO reads data on falling edge
Mode 0 (0,0) (CLK normally low on /CS edges) and Mode 3 (1,1) (CLK normally high on /CS edges) are supported.

Commands:
Enable QPI (38h)
Reset (66h+99h)
Dual SPI operation: Fast Read Dual Output (3Bh), Fast Read Dual I/O (BBh)

BUSY is a r/o bit register (S0) that is set to 1 when chip is executing a:
Page Program, Quad Page Program, Sector Erase, Block Erase, Chip Erase, Write Status Register or
Erase/Program Security Register instruction.

Manufacturer/Device ID 90h: dummy, dummy, 00h, (MF7-MF0), (ID7-ID0)
MF7-0: EFh (Winbond)
ID7-0: 16h

JEDEC ID 9Fh: (MF7-MF0), (ID15-ID8), (ID7-ID0)
MF7-0: EFh (Winbond)
ID15-8:  4017h (SPI), 6017h (QPI)

Write Enable 06h

Volatile SR Write Enable 50h

Write Disable 04h

Read Status Register-1 05h, (S7-0)

Read Status Register-2 35h, (S15-8)

Write Status Register 01h, (S7-S0), (S15-S8)

For 02h/20h/52h/D8h/C7h commands - Must first write WEL=1 by Write Enable 06h (release /CS)

Page Program 02h, A23-A16, A15-A8, A7-A0, D7-D0, D7-D0 (upto 256 data bytes)

Sector Erase (4KB) 20h, A23-A16, A15-A8, A7-A0

Block Erase (32KB) 52h, A23-A16, A15-A8, A7-A0

Block Erase (64KB) D8h, A23-A16, A15-A8, A7-A0

Chip Erase C7h/60h

Power-down B9h

Read Data 03h, A23-A16, A15-A8, A7-A0, (D7-D0)

Fast Read 0Bh, A23-A16, A15-A8, A7-A0, dummy, (D7-D0)

Read Unique ID 4Bh, dummy, dummy, dummy, dummy, (UID63-UID0)

Read SFDP Register 5Ah, 00h, 00h, A7–A0, dummy, (D7-0)

Enable Reset 66h

Reset 99h

## TODOs

* input pipes will break file.seek(0), see possible solution <https://stackoverflow.com/questions/14283025/python-3-reading-bytes-from-stdin-pipe-with-readahead>
* add verbosity param, organize debug prints under verbosity
* add logfile param (default stderr)
* use file.isatty() for enabling terminal logging vs file logging
* infile and outfile text vs. binary mode (stdin/stdout are text / won't work, -i/-o are binary)
* add support for various data file formats (.hex, .srec, etc.)
* add params for explicit file format choice (e.g. for pipes)
* move fixed delays into chip specs
* add specs for mainstream chip IDs
* cleanup docs
* cleanup repo files
* create example/default scripts for making copies
* create upload.sh script
* invent UI for headless use (buttons/LEDs)
