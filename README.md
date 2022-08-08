# pi-spi

This project makes Raspberry Pi into a SPI EEPROM/Flash programmer, e.g. for using it with PC motherboards to fiddle with their CMOS memory.

Either clone Github repo <https://github.com/iva2k/pi-spi> directly to Pi or upload all files to it over SCP/SSH from Windows (if Git is installed on Windows, it has scp implementation) using ```upload.cmd```, then SSH to Pi and run ```install.sh``` from one of subfolders:

* pi-spi.py - python based implementation

TODO: TBD: Once installed, corresponding service will load on boot.

TODO: TBD if Quad-SPI is possible (faster I/O)

Connect SPI device (either probe cable or chip socket) as follows:

| Chip Pin | Chip Signal  | Pi Pin | Pi Signal      | Notes       | My Color |
|:--------:|:------------:|:------:|----------------|-------------|----------|
|  8       | VCC          | 17     | +3.3V          | or GPIO(*)  | Red      |
|  5       | DI (IO0)     | 19     | MOSI / GPIO 10 |             | Yel      |
|  2       | DO (IO1)     | 21     | MISO / GPIO 9  |             | Blu      |
|  6       | CLK          | 23     | SCLK / GPIO 11 |             | Wht      |
|  4       | GND          | 25     | GND            |             | Blk      |
|  1       | /CS          | 24     | CE0 / GPIO 8   | Default     | Grn      |
|  1       | /CS          | 26     | CE1 / GPIO 7   | Alternative | Grn      |
|  3       | /WP (IO2)    | TBD    | +3.3V          | or GPIO(*)  | Org      |
|  7       | /HOLD        | TBD    | +3.3V          | or GPIO(*)  | Gry      |

When using generic SOP8 clips that are wired (e.g. from Amazon, they are very bad knock-offs that very hard to attach so they stay and make contact due to missing key features of the original ones. It's much better to use real ones like Pomona 5250 or 3M 923655-08 / 923650-08), they typically have IDC 2-row connector. The way the wiring is done, chip pins end up in the same geometric arrangement on the connector if connector is placed face down on the chip. Looking at the face of the connector (key is up indicated by ^^):

| 1 | 2^|^3 | 4 |
|---|---|---|---|
| 8 | 7 | 6 | 5 |


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

This project settled on cliff. Other CLI tools of interest:

* Fire: <https://github.com/google/python-fire/blob/master/docs/guide.md>
* Click: <https://click.palletsprojects.com/en/7.x/>

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

### Macronix MX25L6445E

From the datasheet (rev 1.8 Dec 26 2011):

 > For the following instructions: WREN, WRDI, WRSR, SE, BE, BE32K, HPM, CE, PP, CP, 4PP, RDP, DP, WPSEL, SBLK, SBULK, GBLK, GBULK, ENSO, EXSO, WRSCUR, ENPLM, EXPLM, ESRY, DSRY and CLSR the CS# must go high exactly at the byte boundary; otherwise, the instruction will be rejected and not executed.

 For the WRSR instruction it was experimentally established that writing 2 data bytes also rejects the write, must write only 1 data byte. The code was ammended to issue 1-byte write to WRSR. MX25L6406E datasheet contains the same statement, but earlier encounters with that chip (probably) did not exercise the WRSR register writes (as protection was not enabled). 
 
 TODO: Which brings up a desire to make self-contained tests of all operations (round-trip) on each new encountered chip, so the library can "learn" of its bugs. Perhaps a telemetry feature - upon full-chip erase, for chip JEDEC ID not in the database, run all tests to check off all correct operations (collect data on anything failing), then erase again and proceed with intended operations. The risk is to enable protection and not being able to turn it off (e.g. not having control of /WP pin).

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
