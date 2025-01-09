from time import sleep
from smbus2 import SMBus

'''
płytka jest zrobiona niepoprawnie, działać będzie tylko w trybie różnicowym (chyba)
'''

BUS = 1
ADDR = 0x2A

DATA_CH1 = 0x02
DATA_LSB_CH1 = 0x03
RCOUNT_CH1 = 0x09
SETTLECOUNT_CH1 = 0x11
CLOCK_DIVIDERS_CH1 = 0x15
STATUS = 0x18
ERROR_CONFIG = 0x19
CONFIG = 0x1A
MUX_CONFIG = 0x1B
RESET_DEV = 0x1C
DRIVE_CURRENT_CH1 = 0x1F

def init():
    bus = SMBus(BUS)
    # kolejność konfiguracji według datasheetu
    bus.write_word_data(ADDR, RCOUNT_CH1, 0x8329) # nie jestem pewien co to robi
    bus.write_word_data(ADDR, SETTLECOUNT_CH1, 0x10) # to chyba trzeba będzie zgadywać co tu sie dzieje
    bus.write_word_data(ADDR, CLOCK_DIVIDERS_CH1, 0b00_01_00_0110010000) # CH1 100kHz
    bus.write_word_data(ADDR, ERROR_CONFIG, 0b00111_00000_100001) # włącz wszystkie warningi i errory
    bus.write_word_data(ADDR, MUX_CONFIG, 0b0_00_0001000001_001) # ostatnie 001 to chyba najbezpieczniejsza opcja
    bus.write_word_data(ADDR, DRIVE_CURRENT_CH1, 0b10000 << 11)
    _status:int = bus.read_word_data(ADDR, STATUS)
    bus.write_word_data(ADDR, CONFIG, 0b01_0_1_0_1_1_0_0_0_000000) # dużo różnych rzeczy
    if(_status & (0b01 << 14)):
        print("channel 1 error")
    if(_status & (0b01 << 11)):
        print("an active channel has generated a watchdog timeout error")
    if(_status & (0b01 << 10)):
        print("an active channel has generated an amplitude high warning")
    if(_status & (0b01 << 6)):
        print("an active channel has generated an amplitude low warning")

    while(_status & (0b01 << 6)):
        sleep(0.1)



def read_c() -> float:
    bus = SMBus(BUS)
    
    _status:int = bus.read_word_data(ADDR, STATUS)
    if(_status & (0b01 << 14)):
        print("channel 1 error")
    if(_status & (0b01 << 11)):
        print("an active channel has generated a watchdog timeout error")
    if(_status & (0b01 << 10)):
        print("an active channel has generated an amplitude high warning")
    if(_status & (0b01 << 6)):
        print("an active channel has generated an amplitude low warning")
    
    data_ch1 = bus.read_word_data(ADDR, DATA_CH1)
    data_lsb_ch1 = bus.read_word_data(ADDR, DATA_LSB_CH1)
    if data_ch1 & 1000:
        print("AMPLITUDE WARNING")
    
    # rezultat konwersji 
    conv_result = ((data_ch1 & 0xFF00) < 8) | data_lsb_ch1
    
    
    
    return 0.1 # placeholder
    
    
def main():
    init()
    print(read_c())