from time import sleep
from smbus2 import SMBus
from math import pi

'''
płytka jest zrobiona niepoprawnie, działać będzie tylko w trybie różnicowym (chyba)
'''

f_REF = 100e+3 # Hz
L = 100e-6
C = 33e-9

class FDC2212:
    """biblioteka do pracy z płytką rozwojową z układem FDC2212
    """
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

    def __init__(self, i2c_bus=1, address=0x2A):
        self.bus = SMBus(i2c_bus)
        self.address = address

    def initialize(self):
        """Initialize the FDC2x1x with default settings."""
        # kolejność konfiguracji według datasheetu 00 01 00 110010000
        self.bus.write_word_data(self.address, self.CLOCK_DIVIDERS_CH1, 0x0990) # CH1 100kHz 0b00_01_00_0110010000
        self.bus.write_word_data(self.address, self.DRIVE_CURRENT_CH1, 0x7C00)
        self.bus.write_word_data(self.address, self.SETTLECOUNT_CH1, 0x80) # odnieść się do datasheet i sprawdzic co sie dzieje
        self.bus.write_word_data(self.address, self.RCOUNT_CH1, 0x200) # dla rozdzielczości 28 ENOB minimalna wartość to 1074
        self.bus.write_word_data(self.address, self.ERROR_CONFIG, 0x00) # włącz wszystkie warningi i errory 0b00111_00000_0_00001
        self.bus.write_word_data(self.address, self.MUX_CONFIG, 0b0110001000001_001) # ostatnie 001 to chyba najbezpieczniejsza opcja
        self.bus.write_word_data(self.address, self.CONFIG, 0b01_0_1_0_0_1_0_0_0_000000) # dużo różnych rzeczy

    def set_reference_clock_source(self, source: int = 1) -> None:
        """Set the reference clock source .

        Args:
            source (int, optional): (0: internal, 1: external). Defaults to 1.
        """
        config = self.bus.read_word_data(self.address, self.CONFIG)
        config = (config & ~0x0200) | ((source & 0x1) << 9)
        self.bus.write_word_data(self.address, self.CONFIG, config)

    def set_channel_configuration(self, fref_divider: int = 0x190):
        """Konfiguracja wyboru częstotliwości czujnika przez wybranie dzielnika odniesienia dla kanału.

        Args:
            fref_divider (int, optional): wybór dzielnika częstotliwości, minimalnie 0x190, czujnik może pracować maksymalnie przy częstotliwości 100kHz. Defaults to 0x190.
        """
        if fref_divider < 0x190:
            print("dzielnik odniesienia jest zbyt mały, maksymalna częstotliwość z jaką może pracować czujnik to 100kHz")
            return
        value = (1 << 12) | (fref_divider & 0x190)
        self.bus.write_word_data(self.address, self.CLOCK_DIVIDERS_CH1, value)

    def set_drive_current(self, idrive: float = 0.7855):
        """Konfiguracja prądu wysterowania czujnika\n
        1,2 V ≤ amplituda oscylacji czujnika (pk) ≤ 1,8 V\n
        Dla niższych amplitud oscylacji, występuje większy SNR

        Args:
            idrive (float): prąd w mA, wartości od 0.016mA do 1.571mA. Defaults to 0.7855mA
        """
        if (idrive < 0.016) | (idrive > 1.571):
            print("Podano niepoprawy prąd wysterowania czujnika")
            return
        bdrive =  int((idrive / 1.571) * 0x1F)
        value = (bdrive << 11)
        self.bus.write_word_data(self.address, self.DRIVE_CURRENT_CH1, value)

    def set_settling_count(self, count: int = 0x100):
        """ustawienie minimalnego czasu ustalania dla czujnika
        !!! NIE WIADOMO CO SIE DZIEJE< ODNIESC SIE DO DATASHEETA !!!
        Args:
            count (int, optional): ilość cykli do zliczenia, dla rozdzielczości 28 bitów, minimalna wartość to 1074. Defaults to 0x0500.
        """
        self.bus.write_word_data(self.address, self.SETTLECOUNT_CH1, count)

    def set_conversion_time(self, rcount: int = 432):
        """ustawienie licznika referencyjnego dla określonego kanału.

        Args:
            rcount (int, optional): _description_. Defaults to 0x0500.
        """
        self.bus.write_word_data(self.address, self.RCOUNT_CH1, rcount)

    def read_capacitance(self) -> float:
        """odczytaj rezultat konwersji, przelicz i zwróć wartość zmierzonej pojemności czujnika
        Returns:
            float: zmierzona pojemność czujnika[F] (zakładając dokładne wartości rezonatora LC)
        """
        while(self.bus.read_word_data(self.address, self.STATUS) & (0b01 << 6)):
            sleep(0.01)
        
        _status:int = self.bus.read_word_data(self.address, self.STATUS)
        
        if(_status & (0b01 << 14)):
            print("channel 1 error")
        if(_status & (0b01 << 11)):
            print("an active channel has generated a watchdog timeout error")
        if(_status & (0b01 << 10)):
            print("an active channel has generated an amplitude high warning")
        if(_status & (0b01 << 6)):
            print("an active channel has generated an amplitude low warning")

        data_ch1 = self.bus.read_word_data(self.address, self.DATA_CH1)
        data_lsb_ch1 = self.bus.read_word_data(self.address, self.DATA_LSB_CH1)
        # if slef.data_ch1 & 1000:
        #     print("AMPLITUDE WARNING")
        
        # rezultat konwersji 
        conv_result = ((data_ch1 & 0x5FFF) < 16) | data_lsb_ch1
        f_sensor: float = (conv_result * f_REF) / pow(2, 28)
        C_sensor: float = 1 / (L * pow((2 * pi * f_sensor), 2)) - C
        return C_sensor