import opcode
from termios import TCXONC
from time import sleep
from smbus2 import SMBus, i2c_msg
import os

HC_CLOCK: float = 4e6
LS_CLOCK: float = 32768

"""
The PCap04 standard firmware provides capacitance and temperature measurement results as raw ratio. Thereby, the firmware considers the configuration settings and delivers the results accordingly. The following modes/features are supported (not exhaustive):
•	Capacitance ratio (C_ratio)
•	Temperature (R_ratio)
•	Pulse output (PWM/PDM)
•	Stray compensation

Result registers (see comments in header):
RES0 .... 5 : Capacitance Ratios for Capacitance Ports PC0.....5
RES6: Resistance Ratio for External Sensor at Port PT1, w.r.t. Internal or External reference
RES7: Resistance Ratio for Internal sensor, w.r.t. Internal or External reference
PULSE0 & PULSE1:	Pulse Outputs
"""

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
    '''  ...'''
    CFG47 = 0x2F
    CFG48 = 0x31
    CFG49 = 0x32
    CFG50 = 0x33
    '''  ...'''
    CFG54 = 0x36
    '''  ...'''
    CFG62 = 0x3E
    CFG63 = 0x3F
    
    with open("/home/surban/Public/k5w-przetworniki/firmware/PCap04_standard_v1.hex", 'r') as file:
        hex_values = []
        for line in file:
            line = line.strip()
            for hex_str in line.split():
                hex_int = int(hex_str, 16)
                hex_values.append(hex_int)
    
    OPCODE = {
        "wr_mem": 0xA000,
        "rd_mem": 0x20,
        "wr_config": 0xA3C0,
        "rd_congig": 0x23C0,
        "rd_res": 0x40,
        "POR": 0x88,
        "init": 0x8A,
        "CDC_start": 0x8C,
        "RDC_start": 0x8E,
        "dsp_trig": 0x8D,
        "nv_store": 0x96,
        "nv_recall": 0x99,
        "nv_erase": 0x9C,
        "test_read": 0x7E11
    }
    
    def __init__(self, bus=1, address=0x28 ) :
        self.bus = SMBus(bus)
        self.address = address
        
    def i2c_memory_write(self, address: int, firmware: list):
        opcode = 0xA0
        i2ctx = []
        
        i2ctx.append(opcode | (address >> 8))
        i2ctx.append(address)
        for i in range(0, len(firmware)):
            i2ctx.append(firmware[i])
        
        tx = i2c_msg.write(self.address, i2ctx)
        self.bus.i2c_rdwr(tx)
        
    def i2c_memory_read(self, address: int, len: int) -> list:
        opcode = 0x20
        hex_values = []
        
        wr = i2c_msg.write(self.address, [opcode | (address >> 8), address])
        rd = i2c_msg.read(self.address, len)
        self.bus.i2c_rdwr (wr, rd)
        
        return list(rd) # type: ignore
    
    def i2c_congig_write(self, address: int, config: int):
        opcode = 0xA3C0
        i2ctx = []
        
        i2ctx.append(opcode >> 8)
        i2ctx.append((opcode & 0xFF) | address)
        i2ctx.append(config)
        
        tx = i2c_msg.write(self.address, i2ctx)
        self.bus.i2c_rdwr(tx)
        
    def i2c_result_read(self, address: int) -> int:
        opcode = 0x40
        
        wr = i2c_msg.write(self.address, [(opcode >> 8), ((opcode & 0xFF) | address)])
        rd = i2c_msg.read(self.address, 1)
        self.bus.i2c_rdwr (wr, rd)
        return int(rd)
        
    def read_register_nvram(self, reg) -> int:
        self.bus.write_i2c_block_data(self.address, reg + self.OPCODE["rd_mem"], reg)
        return self.bus.read_byte(self.address)
            
    def write_register_nvram(self, reg, data):
        """Write to NVRAM"""
        try:
            self.bus.write_block_data(self.address, reg + (self.OPCODE["wr_mem"] >> 8), [reg, data])
        except:
            print(f"Error writing to NVRAM {hex(reg)}")
    
    def initialize(self):
        self.bus.write_byte(self.address, 0x8A)
        # self.write_register(self.CFG00, 0x00) # ???
        # self.write_register(self.CFG01, 0x00) # ???
        # self.write_register(self.CFG02, 0x00) # zostawić default
        # self.write_register(self.CFG03, 0x00) # ???
        # self.write_register(self.CFG04, 0x91) # ???
        # self.write_register(self.CFG05, 0x00) # ???
        # self.write_register(self.CFG06, 0x03) # ???
        # self.write_register(self.CFG07, 0xFF) # ???
        # self.write_register(self.CFG08, 0x00) # ???
        # self.write_register(self.CFG09, 0x00) # ???
        # self.write_register(self.CFG10, 0x00) # ???
        # self.write_register(self.CFG11, 0x00) # ???
        # self.write_register(self.CFG12, 0x00) # ???
        
    def read_capacitance(self, reg) -> int:
        return self.read_register_nvram(reg)
    
    def test(self):
        self.i2c_memory_write(0, self.hex_values[0:len(self.hex_values) - 2])
        self.i2c_congig_write(47, 0x01) # runbit
        
        while True:
            print(self.i2c_result_read())
        # temp = self.i2c_memory_read(0, len(self.hex_values) - 2)
        # print(temp)
        
        # self.bus.write_byte(self.address, 0x88)
        # self.bus.write_byte(self.address, 0x8C)
        # sleep(0.1)
        # print("STATUS_0: ", bin(self.bus.read_byte_data(self.address, 0x40 + 32)))
        # print("STATUS_1: ", bin(self.bus.read_byte_data(self.address, 0x40 + 33)))
        # print("STATUS_2: ", bin(self.bus.read_byte_data(self.address, 0x40 + 34)))
        
        # print([0 + (self.OPCODE["wr_mem"] & 0x00FF)] + self.hex_values)
        
        # for i in range(0, 4):
        #     print("CDC reg: ",i , self.bus.read_byte_data(self.address, 0x40 + i))    
        