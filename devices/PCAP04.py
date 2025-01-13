from time import sleep
from smbus2 import SMBus
import os

HC_CLOCK: float = 4e6
LS_CLOCK: float = 32768

class PCAP04:
    def __init__(self, bus=1, address=0x50 ) : # ???
        """Initialize PCAP04"""
        self.bus = SMBus(bus)
        self.address = address
    
    def initialize(self):
        pass