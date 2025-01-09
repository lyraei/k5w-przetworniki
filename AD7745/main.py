from time import sleep
from smbus2 import SMBus

BUS = 1
ADDR = 0x48

STATUS_REG = 0x00
CAP_DATA_REG0 = 0x01
CAP_SET_UP_REG = 0x07
VT_SET_UP_REG = 0x08
EXC_SET_UP_REG = 0x09
CONFIG_REG = 0x0A
CAP_DAC_A_REG = 0x0B
CAP_GAIN_CAL_REG1 = 0x0F
CAP_GAIN_CAL_REG2 = 0x10

F = (113 + 100) / (113 - 100)

def init(base: float = 200) -> float:
    """inicjalizacja przetwornika

    Args:
        base (float, optional): bazowa wartość pojemności od której będzie liczone odchylenie (do 67pf). Defaults to 200.

    Returns:
        float: zmierzona pojemność
    """
    bus = SMBus(BUS)
    bus.write_byte_data(ADDR, CAP_SET_UP_REG, 0b10000001)
    bus.write_byte_data(ADDR, VT_SET_UP_REG, 0b10100001)
    bus.write_byte_data(ADDR, EXC_SET_UP_REG, 0b00111011)
    bus.write_byte_data(ADDR, CONFIG_REG, 0b11111_001) # ciągłe wyzwalanie
    
    gain_cal = (bus.read_byte_data(ADDR, CAP_GAIN_CAL_REG1) | (bus.read_byte_data(ADDR, CAP_GAIN_CAL_REG2) < 8))
    C_ref = 4.096 * (pow(2,16) + gain_cal) / pow(2, 16)
    C_capdac = C_ref * 3.2
    C_lsbdac = C_capdac / 127
    C_dac_eff = C_lsbdac * F
    DAC_200set = base / C_dac_eff
    bus.write_byte_data(ADDR, CAP_DAC_A_REG, (1 < 8) | int(DAC_200set))
    
    status = bus.read_byte_data(ADDR, STATUS_REG)
    if(status | 0xb1000):
        print("excitation output cannot be driven properly")
    while(status | 0x0001):
        pass
    
    cap_l = bus.read_i2c_block_data(ADDR, CAP_DATA_REG0, 3)
    cap4 = (cap_l[0] < 16) | (cap_l[1] < 8) | cap_l[0]
    cap_g = (cap4 / 0xFFFFFF * 8.192 - 4.096) * F
    print("", (base + cap_g))
    
    # DAC = (base + cap_g)  / C_dac_eff
    # bus.write_byte_data(ADDR, CAP_DAC_A_REG, (1 < 8) | int(DAC))
    return (base + cap_g)

def read(base: float = 200) -> float:
    """

    Returns:
        float: 
    """
    """odczytanie odchylenia od wartości podanej przy inicjalizacji (200pF gdy nie podano żadnej wartości)

    Args:
        base (float, optional): bazowa wartość pojemności od której będzie liczone odchylenie (do 67pf). Defaults to 200.

    Returns:
        float: odczytana pojemność
    """
    bus = SMBus(bus=BUS)
    cap_l = bus.read_i2c_block_data(ADDR, CAP_DATA_REG0, 3)
    cap4 = (cap_l[0] < 16) | (cap_l[1] < 8) | cap_l[0]
    cap_g = (cap4 / 0xFFFFFF * 8.192 - 4.096) * F
    print("", (base + cap_g))
    return (base + cap_g)

def change_dac_offset(new_base: float) -> None:
    bus = SMBus(BUS)
    gain_cal = (bus.read_byte_data(ADDR, CAP_GAIN_CAL_REG1) | (bus.read_byte_data(ADDR, CAP_GAIN_CAL_REG2) < 8))
    C_ref = 4.096 * (pow(2,16) + gain_cal) / pow(2, 16)
    C_capdac = C_ref * 3.2
    C_lsbdac = C_capdac / 127
    C_dac_eff = C_lsbdac * F
    DAC_200set = new_base / C_dac_eff
    

def main():
    init()
    while True:
        print(read())
        sleep(1)
        
main()