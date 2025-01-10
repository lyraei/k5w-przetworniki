from time import sleep
from smbus2 import SMBus
import os

HC_CLOCK: float = 4e6
LS_CLOCK: float = 32768

def init():
    pass

def program_chip():
    file = os.open("./program.hex", os.O_RDONLY)