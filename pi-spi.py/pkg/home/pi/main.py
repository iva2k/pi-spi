#!/usr/bin/python
from __future__ import print_function
#?from future.utils import viewitems

debug = True
stopshortfile = False
writedryrun = True

import argparse

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
except:
    print('RPi.GPIO: incompatible platform, using rpidevmocks.MockGPIO')
    from rpidevmocks import MockGPIO
    GPIO = MockGPIO()


#import gpiozero

#helpers -------------------------------------------------------------------------------
def print_status(status):
    print('status %s %s' % (bin(status[1])[2:].zfill(8), bin(status[0])[2:].zfill(8)))

def print_page(page):
    s = ''
    for row in range(16):
        for col in range(16):
            addr = row * 16 + col
            if (addr < len(page)):
                s += '%02X ' % page[addr]
        s += '\n'
    print(s) 

def ReverseBits(byte):
    byte = ((byte & 0xF0) >> 4) | ((byte & 0x0F) << 4)
    byte = ((byte & 0xCC) >> 2) | ((byte & 0x33) << 2)
    byte = ((byte & 0xAA) >> 1) | ((byte & 0x55) << 1)
    return byte
#end def

def BytesToHex(Bytes):
    return ''.join(['0x%02X ' % x for x in Bytes]).strip()
#end def

chip = None
def init_chip():
    # Setup GPIO, Open chip
    global chip
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup (SPI_VCC , GPIO.OUT, initial=GPIO.HIGH)
    GPIO.setup (SPI_WP  , GPIO.OUT, initial=GPIO.HIGH)
    GPIO.setup (SPI_HOLD, GPIO.OUT, initial=GPIO.HIGH)
    chip = spiflash(bus = SPI, cs = CS, options = {
        'max_speed_hz': 16000000,     # RPi has issue with speed higher than 16MHz.
        'id_speed_hz' : 1000000,
    })    

init_chip()

# Using argparse?
# parser = argparse.ArgumentParser(description='Process some integers.')
# parser.add_argument('integers', metavar='N', type=int, nargs='+', help='an integer for the accumulator')
# parser.add_argument('--sum', dest='accumulate', action='store_const', const=sum, default=max, help='sum the integers (default: find the max)')
# args = parser.parse_args()
# print( args.accumulate(args.integers) )

# tests()





# Using cliff?

import sys

from cliff.app import App
from cliff.command import Command
from cliff.commandmanager import CommandManager
from cliff.show import ShowOne

class DemoApp(App):

    def __init__(self):
        super(DemoApp, self).__init__(
            description='cliff demo app',
            version='0.1',
            command_manager=CommandManager('DemoApp'),
            deferred_help=True,
            )

    def initialize_app(self, argv):
        self.LOG.debug('initialize_app')
        commands = {
            'test'   : Test   ,
            'read'   : Read   ,
            'verify' : Verify ,
            'write'  : Write  ,
        }
        for k, v in iter(commands.items()):
            self.command_manager.add_command(k, v)

    def prepare_to_run_command(self, cmd):
        self.LOG.debug('prepare_to_run_command %s', cmd.__class__.__name__)

    def clean_up(self, cmd, result, err):
        self.LOG.debug('clean_up %s', cmd.__class__.__name__)
        if err:
            self.LOG.debug('got an error: %s', err)

#TESTS -------------------------------------------------------------------
class Test(Command):
    'read data from device'

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        #? parser.add_argument('from', nargs='?', help='start address to read the data from', default='start')
        return parser

    def take_action(self, parsed_args):
        global chip, debug
        print('read JEDEC ID...')
        jedec_id = chip.read_jedec_id()
        jedec_id = jedec_id[0] << 16 | jedec_id[1] << 8 | jedec_id[2] << 0
        print('JEDEC ID:%06X' % (jedec_id))

        print('read Chip Specs...')
        specs = chip.chip_specs()
        print('Chip specs:', specs if specs else ' unknown chip')

        #print_status(read_status())
        #write_disable()
        #print_status(read_status())

        print('checking busy...')
        chip.wait_until_not_busy()
        print('reading page...')
        p = chip.read_page(0, 0)
        print_page(p)

        #print 'erasing chip'
        #chip.erase_all()
        #print 'chip erased'

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

# Expression Calculator (from https://stackoverflow.com/a/33030616)
import ast
import operator
_OP_MAP = {
    ast.Add : operator.add,
    ast.Sub : operator.sub,
    ast.Mult: operator.mul,
    #ast.Div : operator.div, # Python2
    ast.Div : operator.truediv, # Python3
    ast.Invert: operator.neg,
}
class Calc(ast.NodeVisitor):
    def visit_BinOp(self, node):
        left = self.visit(node.left)
        right = self.visit(node.right)
        return _OP_MAP[type(node.op)](left, right)
    def visit_Num(self, node):
        return node.n
    def visit_Expr(self, node):
        return self.visit(node.value)
    @classmethod
    def subst_values(cls, values, text):
        for key, value in values.items():
            text = text.replace(key, str(value) )
        return text
    @classmethod
    def evaluate(cls, expression):
        tree = ast.parse(expression)
        calc = cls()
        return calc.visit(tree.body[0])

class SpiCommand(Command):
    'base class for Spi commands'

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument('-f', '--from'   , dest='addr_from', nargs='?',                               default='start'   , help='start address to read the data from, can be formula using {start,end,page} variables, default=start' )
        parser.add_argument('-t', '--to'     , dest='addr_to'  , nargs='?',                               default='end'     , help='end   address to read the data   to, can be formula using {start,end,page} variables, default=end'   )
        parser.add_argument('--speed'        , dest='speed'    , nargs='?', type=int                    , default=0         , help='max SPI speed (Hz)' )
        return parser

    def preparse_args(self, parsed_args):
        global chip, debug
        if (debug):
            print('prepare_args(', parsed_args,')')
        specs = chip.chip_specs()
        pagesize = 256
        
        # Cleanup / resolve parameters
        subs = {
            'start': 0,
            'end'  : specs['size'],
            'page' : pagesize,
        }
        parsed_args.addr_from = Calc.evaluate(Calc.subst_values(subs, str(parsed_args.addr_from)))
        parsed_args.addr_to   = Calc.evaluate(Calc.subst_values(subs, str(parsed_args.addr_to  )))
        #if (debug):
        #    print('prepare_args() output=', parsed_args)
        return parsed_args

class Read(SpiCommand):
    'read data from device'

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument('-o', '--outfile', dest='outfile'  , nargs='?', type=argparse.FileType('wb'), default=sys.stdout, help='output (data) file' )
        return parser

    def take_action(self, parsed_args):
        parsed_args = super().preparse_args(parsed_args)
        global chip, debug
        
        total_errors = chip.read(parsed_args.addr_from, parsed_args.addr_to, parsed_args.outfile, {
            'debug'         : debug,
            'stopshortfile' : stopshortfile,
            'writedryrun'   : writedryrun,
            'speed'         : parsed_args.speed,
        })
        if (total_errors == -1):
            raise argparse.ArgumentTypeError('ADDR_TO value has to be more than ADDR_FROM')
        if (total_errors == -2):
            raise argparse.ArgumentTypeError('ADDR_TO value has to be not more than chip size')
        return total_errors

class Verify(SpiCommand):
    'verify data in device'

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument('-i', '--infile' , dest='infile'   , nargs='?', type=argparse.FileType('rb'), default=sys.stdin , help='input (data) file' )
        parser.add_argument('-o', '--outfile', dest='outfile'  , nargs='?', type=argparse.FileType('wb'), default=sys.stdout, help='output (diff) file' )
        return parser

    def take_action(self, parsed_args):
        parsed_args = super().preparse_args(parsed_args)
        global chip, debug
        
        # Implementnation:
        total_errors = chip.verify(parsed_args.addr_from, parsed_args.addr_to, parsed_args.infile, parsed_args.outfile, {
            'debug'         : debug,
            'stopshortfile' : stopshortfile,
            'writedryrun'   : writedryrun,
            'speed'         : parsed_args.speed,
        })
        if (total_errors == -1):
            raise argparse.ArgumentTypeError('ADDR_TO value has to be more than ADDR_FROM')
        if (total_errors == -2):
            raise argparse.ArgumentTypeError('ADDR_TO value has to be not more than chip size')
        return total_errors

class Write(SpiCommand):
    'write data to device'

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument('-i', '--infile' , dest='infile'   , nargs='?', type=argparse.FileType('rb'), default=sys.stdin , help='input (data) file' )
        parser.add_argument('-o', '--outfile', dest='outfile'  , nargs='?', type=argparse.FileType('wb'), default=sys.stdout, help='output (diff) file' )
        parser.add_argument('--erase'        , dest='erase'    , action='store_true'                                        , help='erase data range in device before write' )
        parser.add_argument('--verify'       , dest='verify'   , action='store_true'                                        , help='verify device data after write' )
        return parser

    def take_action(self, parsed_args):
        parsed_args = super().preparse_args(parsed_args)
        global chip, debug
        
        # Implementnation:
        total_errors = 0
        if (parsed_args.erase):
            total_errors = chip.erase(parsed_args.addr_from, parsed_args.addr_to, {
                'debug'         : debug,
                'stopshortfile' : stopshortfile,
                'writedryrun'   : writedryrun,
                'speed'         : parsed_args.speed,
            })
            if (total_errors != 0):
                return total_errors

        total_errors = chip.write(parsed_args.addr_from, parsed_args.addr_to, parsed_args.infile, {
            'debug'         : debug,
            'stopshortfile' : stopshortfile,
            'writedryrun'   : writedryrun,
            'speed'         : parsed_args.speed,
        })
        if (total_errors != 0):
            return total_errors

        if (parsed_args.verify):
            total_errors = chip.verify(parsed_args.addr_from, parsed_args.addr_to, parsed_args.infile, parsed_args.outfile, {
                'debug'         : debug,
                'stopshortfile' : stopshortfile,
                'writedryrun'   : writedryrun,
                'speed'         : parsed_args.speed,
            })
            if (total_errors == -1):
                raise argparse.ArgumentTypeError('ADDR_TO value has to be more than ADDR_FROM')
            if (total_errors == -2):
                raise argparse.ArgumentTypeError('ADDR_TO value has to be not more than chip size')
        return total_errors

def main(argv=sys.argv[1:]):
    myapp = DemoApp()
    return myapp.run(argv)

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
