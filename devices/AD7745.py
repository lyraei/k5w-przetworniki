from time import sleep
from smbus2 import SMBus

class AD7745:
    # register addresses
    STATUS_REG = 0x00
    CAP_DATA_H = 0x01 
    CAP_DATA_M = 0x02
    CAP_DATA_L = 0x03
    CAP_SETUP = 0x07
    SETUP_REG = 0x08
    EXC_SETUP = 0x09
    CONFIGURATION = 0x0A
    CAP_DAC_A = 0x0B
    CAP_DAC_B = 0x0C
    CAP_GAIN_CAL_REG1 = 0x0F
    CAP_GAIN_CAL_REG2 = 0x10
    # gain
    F = (113 + 100) / (113 - 100)
    
    def __init__(self, bus=1, address=0x48):
        """Initialize AD7745"""
        self.bus = SMBus(bus)
        self.address = address
        # reset device
        self.reset()
        
    def reset(self):
        self.bus.write_byte(self.address, 0xBF)
        sleep(0.2) # Wait for reset to complete
            
    def read_register(self, reg) -> int:
        """Read a register"""
        try:
            return self.bus.read_byte_data(self.address, reg)
        except:
            print(f"Error reading register {reg}")
            return -1
            
    def write_register(self, reg, data):
        """Write to a register"""
        try:
            self.bus.write_byte_data(self.address, reg, data)
        except:
            print(f"Error writing to register {reg}")

    def initialize(self, base: float = 200):
        """Configure for single-ended capacitive measurement"""
        self.write_register(self.CAP_SETUP, 0x81)
        self.write_register(self.SETUP_REG, 0xA1)
        self.write_register(self.EXC_SETUP, 0x1B)
        self.write_register(self.CONFIGURATION, 0x21)
        
        gain_cal = (self.read_register(self.CAP_GAIN_CAL_REG1) | (self.read_register(self.CAP_GAIN_CAL_REG2) < 8))
        C_ref = 4.096 * (pow(2,16) + gain_cal) / pow(2, 16)
        C_capdac = C_ref * 3.2
        C_lsbdac = C_capdac / 127
        C_dac_eff = C_lsbdac * self.F
        DAC_200set = base / C_dac_eff
        dac_a_reg = int(DAC_200set) & 0x7F
        dac_b_reg = (int(DAC_200set) >> 8) & 0x7F
        
        self.write_register(self.CAP_DAC_A, (1 << 8) | dac_a_reg)
        self.write_register(self.CAP_DAC_B, (1 << 8) | dac_b_reg)
        
    def change_dac_offset(self, base: float):
        gain_cal = (self.read_register(self.CAP_GAIN_CAL_REG1) | (self.read_register(self.CAP_GAIN_CAL_REG2) < 8))
        C_ref = 4.096 * (pow(2,16) + gain_cal) / pow(2, 16)
        C_capdac = C_ref * 3.2
        C_lsbdac = C_capdac / 127
        C_dac_eff = C_lsbdac * self.F
        DAC = base  / C_dac_eff
        dac_a_reg = int(DAC) & 0x7F
        dac_b_reg = (int(DAC) >> 8) & 0x7F
        
        self.write_register(self.CAP_DAC_A, (1 << 8) | dac_a_reg)
        self.write_register(self.CAP_DAC_B, (1 << 8) | dac_b_reg)

    def read_capacitance(self, base: float = 200):
        """odczytanie odchylenia pojemności od wartości bazowej

        Args:
            base (float, optional): zerowa pojemność od której liczone jest odchylenie (dodatnie lub ujemne). Defaults to 200.

        Returns:
            float: pojemność czujnika[pF]
        """
        # check if data is ready
        status = self.read_register(self.STATUS_REG)
        if not status & 0x01:  # RDYCAP bit
            return None
            
        # read 3 bytes of capacitance data
        try:
            data_h = self.read_register(self.CAP_DATA_H)
            data_m = self.read_register(self.CAP_DATA_M)
            data_l = self.read_register(self.CAP_DATA_L)
            
            # combine bytes into 24-bit value
            raw_value = (data_h << 16) | (data_m << 8) | data_l
            
            # convert to capacitance in pF
            # dynamic range is ±67.11pF
            capacitance = (float(raw_value) / 0xFFFFFF * 8.192 - 4.096) * self.F
            
            return capacitance + base
            
        except:
            print("Error reading capacitance")
            return None
        
    def check_status(self):
        """Read status register"""
        status = self.read_register(self.STATUS_REG)
        if status is not None:
            return {
                'excitation_error': bool(status & 0x08),
                'conversion_complete': bool(status & 0x04),
                'voltage_temp_ready': bool(status & 0x02),
                'capacitance_ready': bool(status & 0x01)
            }
        return None