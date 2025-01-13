from time import sleep
from smbus2 import SMBus
import os

HC_CLOCK: float = 4e6
LS_CLOCK: float = 32768

class PCAP04:
    
    CFG00 = 0x00
    CFG01 = 0x01
    CFG02 = 0x02
    CFG03 = 0x03
    CFG04 = 0x04
    CFG05 = 0x05
    CFG06 = 0x06
    CFG07 = 0x07
    CFG08 = 0x08
    CFG09 = 0x09
    CFG10 = 0x0A
    CFG11 = 0x0B
    CFG12 = 0x0C
    CFG13 = 0x0D
    CFG14 = 0x0E
    CFG15 = 0x0F
    CFG16 = 0x10
    CFG17 = 0x11
    CFG18 = 0x12
    CFG19 = 0x13
    CFG20 = 0x14
    CFG21 = 0x15
    CFG22 = 0x16
    CFG23 = 0x17
    CFG24 = 0x18
    CFG25 = 0x19
    CFG26 = 0x1A
    CFG27 = 0x1B
    CFG28 = 0x1C
    CFG29 = 0x1D
    CFG30 = 0x1E
    CFG31 = 0x1F
    CFG32 = 0x20
    CFG33 = 0x21
    CFG34 = 0x22
    CFG35 = 0x23
    CFG36 = 0x24
    CFG37 = 0x25
    CFG38 = 0x26
    CFG39 = 0x27
    CFG40 = 0x28
    CFG41 = 0x29
    CFG42 = 0x2A
    ''' ..... '''
    CFG47 = 0x2F
    CFG48 = 0x31
    CFG49 = 0x32
    CFG50 = 0x33
    ''' ..... '''
    CFG54 = 0x36
    ''' ..... '''
    CFG62 = 0x3E
    CFG63 = 0x3F
    
    def __init__(self, bus=1, address=0x50 ) : # ¿¿¿0x50???
        """initialize PCAP04"""
        self.bus = SMBus(bus)
        self.address = address
    
    def initialize(self):
        self.bus.write_byte_data(self.address, self.CFG00, 0x0) # ???
        self.bus.write_byte_data(self.address, self.CFG01, 0x0) # ???
        # self.bus.write_byte_data(self.address, self.CFG02, 0x) zostawić default
        self.bus.write_byte_data(self.address, self.CFG03, 0x0) # ???
        self.bus.write_byte_data(self.address, self.CFG04, 0x91) # ???
        self.bus.write_byte_data(self.address, self.CFG05, 0x00) # ???
        self.bus.write_byte_data(self.address, self.CFG06, 0x03) # ???
        self.bus.write_byte_data(self.address, self.CFG07, 0xFF) # ???
        self.bus.write_byte_data(self.address, self.CFG08, 0x00) # ???
        self.bus.write_byte_data(self.address, self.CFG09, 0x) # ???
        self.bus.write_byte_data(self.address, self.CFG10, 0x) # ???
        self.bus.write_byte_data(self.address, self.CFG11, 0x) # ???
        self.bus.write_byte_data(self.address, self.CFG12, 0x) # ???