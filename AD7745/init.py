from smbus2 import SMBus

BUS = 1
ADDR = 0x48

CAP_SET_UP_REG = 0x07
VT_SET_UP_REG = 0x08
EXC_SET_UP_REG = 0x09
CONFIG_REG = 0x0A
CAP_DAC_A_REG = 0x0B

def init():
    """inicjalizacja przetwornika AD7745
    """
    bus = SMBus(1)
    bus.write_byte_data(ADDR, CAP_SET_UP_REG, 0b10000001)
    bus.write_byte_data(ADDR, VT_SET_UP_REG, 0b10100001)
    bus.write_byte_data(ADDR, EXC_SET_UP_REG, 0b00111011)
    bus.write_byte_data(ADDR, CONFIG_REG, 0b11111_001) # ciągłe wyzwalanie
    bus.write_byte_data(ADDR, CAP_DAC_A_REG, 0x0)
    
    