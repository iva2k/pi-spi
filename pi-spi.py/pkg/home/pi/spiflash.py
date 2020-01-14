#!/usr/bin/python
from __future__ import print_function

WREN = 0x06
WRDI = 0x04
RDSR = 0x05
RDSR2 = 0x35
WRSR = 1
READ = 0x03
WRITE = 0x02
SECTOR_ERASE = 0x20
CHIP_ERASE = 0xC7
JEDEC_ID = 0x9F

# Time in milliseconds:
MAXWAIT = 5000
WAITSTEP = 5
WAITWREN = 5
WAITWRDIS = 5

def Mbit(n):
    return n * int(1024*1024/8)

def MHz(n):
    return n * 1000000

from time import sleep
# from datetime import datetime
try:
    import spidev
except:
    print("spidev: incompatible platform, using rpidevmocks.MockSpidev")
    from rpidevmocks import MockSpidev
    spidev = MockSpidev()

def sleep_ms(msecs):
    sleep(float(msecs) / 1000.0)

class spiflash(object):

    chips = {
# JEDEC ID collection (Page=256 Bytes)
# Chip          Mfr Type ID Size(Mbit) Sector(kB) Blocks(kB) Voltage Speed(MHz) (ms):ErzChip:ErzSector:WrPage
#                                                                    [Rd<3V/Rd/Other<3V/Other]
# SST26VF016    BFH 26H 01H 16         4          8,32,64    2.7-3.6  80        35:18:1
# SST26VF032    BFH 26H 02H 32         4          8,32,64    2.7-3.6  80        35:18:1
# W25Q64FV      EFH 40H 17H 64         4          32,64      2.7-3.6 33/50/80/104  35:18:1
        0xEF4017: { 'size': Mbit(64), 'speed': MHz(33)},
# W25Q64FV(QPI) EFH 60H 17H 64         4          32,64      2.7-3.6 33/50/80/104  35:18:1
    }
    
    def __init__(self, bus, cs, mode = 0, max_speed_hz = 1000000):
        print("spiflash.__init__(bus=",bus, ", cs=", cs, ")")
        self.spi = spidev.SpiDev()
        self.spi.open(bus, cs)       
        self.spi.max_speed_hz = int(max_speed_hz)
        self.spi.mode = mode
        # self.spi.bits_per_word = 0

    def __del__(self):
        try:
            self.spi.close()
        except:
            pass

    def speed_set(self, speed_hz):
        self.spi.max_speed_hz = int(speed_hz)

    def speed_get(self):
        return self.spi.max_speed_hz

    # reads ----------------------------------------------------------------------------------
    def read_status(self):
        statreg = self.spi.xfer2([RDSR,RDSR])[1]
        statreg2 = self.spi.xfer2([RDSR2,RDSR2])[1]
        return statreg, statreg2

    def read_page(self, addr1, addr2):
        xfer = [READ, addr1, addr2, 0] + [255 for _ in range(256)] # command + 256 dummies
        return self.spi.xfer2(xfer)[4:] #skip 4 first bytes (dummies)

    # writes ----------------------------------------------------------------------------------
    def write_enable(self):
        self.spi.xfer2([WREN])
        # sleep_ms(WAITWREN)

    def write_disable(self):
        self.spi.xfer2([WRDI])
        # sleep_ms(WAITWRDIS)

    def write_status(self,s1,s2):
        self.write_enable()
        sleep_ms(WAITWREN)
        self.spi.xfer2([WRSR,s1,s2])
        # sleep_ms(10)
        self.wait_until_not_busy()

    def write_page(self, addr1, addr2, page):
        self.write_enable()
        sleep_ms(WAITWREN)
        xfer = [WRITE, addr1, addr2, 0] + page[:256]
        self.spi.xfer2(xfer)
        # sleep_ms(10)
        self.wait_until_not_busy()

    def write_and_verify_page(self, addr1, addr2, page):
        self.write_page(addr1, addr2, page)
        return self.read_page(addr1, addr2)[:256] == page[:256]

    # erases ----------------------------------------------------------------------------------
    def erase_sector(self, addr1, addr2):
        self.write_enable()
        sleep_ms(WAITWREN)
        xfer = [SECTOR_ERASE, addr1, addr2, 0]
        self.spi.xfer2(xfer)
        # sleep_ms(10)
        self.wait_until_not_busy()

    def erase_all(self):
        self.write_enable()
        sleep_ms(WAITWREN)
        self.spi.xfer2([CHIP_ERASE])
        # sleep_ms(10)
        self.wait_until_not_busy()

    # misc ----------------------------------------------------------------------------------

    # Wait for the chip. Timeout after MAXWAIT
    def wait_until_not_busy(self):
        max_wait = MAXWAIT
        statreg = self.spi.xfer2([RDSR,RDSR])[1]
        while (statreg & 0x1) == 0x1:
            if (max_wait < 0):
                #print("")
                raise UserWarning('Timeout waiting %dms for device ready, statreg=%02X' % (MAXWAIT, statreg) )
            sleep_ms(WAITSTEP)
            #print(".", end=" ")
            #print "%r \tRead %X" % (datetime.now(), statreg)
            statreg = self.spi.xfer2([RDSR,RDSR])[1]
            max_wait -= WAITSTEP

    def read_jedec_id(self):
        data = self.spi.xfer2([JEDEC_ID,0,0,0])
        manufacturer_id = data[1]
        memory_type = data[2]
        capacity = data[3]
        return (manufacturer_id, memory_type, capacity)

    def chip_specs(self):
        data = self.read_jedec_id()
        key = data[0] << 16 | data[1] << 8 | data [2] << 0
        self.specs = self.chips.get(key)
        return self.specs
