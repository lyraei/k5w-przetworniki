from time import sleep
from regex import D
from smbus2 import SMBus

'''
płytka jest zrobiona niepoprawnie, działać będzie tylko w trybie różnicowym (chyba)
'''

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

class FDC2212:
    """biblioteka do pracy z płytką rozwojową z układem FDC2212
    """
    def __init__(self, i2c_bus=1, address=0x2A) -> None:
        self.bus = SMBus(i2c_bus)
        self.address = address

    def initialize(self):
        """Initialize the FDC2x1x with default settings."""
        # kolejność konfiguracji według datasheetu
        self.bus.write_word_data(self.address, RCOUNT_CH1, 0x432) # dla rozdzielczości 28 ENOB minimalna wartość to 1074
        self.bus.write_word_data(self.address, SETTLECOUNT_CH1) # odnieść się do datasheet i sprawdzic co sie dzieje
        self.bus.write_word_data(self.address, CLOCK_DIVIDERS_CH1, 0b00_01_00_0110010000) # CH1 100kHz
        self.bus.write_word_data(self.address, ERROR_CONFIG, 0b00111_00000_100001) # włącz wszystkie warningi i errory
        self.bus.write_word_data(self.address, MUX_CONFIG, 0b0_00_0001000001_001) # ostatnie 001 to chyba najbezpieczniejsza opcja
        self.bus.write_word_data(self.address, DRIVE_CURRENT_CH1, 0b10000 << 11)
        _status:int = self.bus.read_word_data(self.address, STATUS)
        self.   bus.write_word_data(self.address, CONFIG, 0b01_0_1_0_1_1_0_0_0_000000) # dużo różnych rzeczy
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

    def set_reference_clock_source(self, source: int = 1) -> None:
        """Set the reference clock source .

        Args:
            source (int, optional): (0: internal, 1: external). Defaults to 1.
        """
        config = self.bus.read_word_data(self.address, CONFIG)
        config = (config & ~0x0200) | ((source & 0x1) << 9)
        self.bus.write_word_data(self.address, CONFIG, config)

    def set_channel_configuration(self, fref_divider: int = 0x190):
        """Konfiguracja wyboru częstotliwości czujnika przez wybranie dzielnika odniesienia dla kanału.

        Args:
            fref_divider (int, optional): wybór dzielnika częstotliwości, minimalnie 0x190, czujnik może pracować maksymalnie przy częstotliwości 100kHz. Defaults to 0x190.
        """
        if fref_divider < 0x190:
            print("dzielnik odniesienia jest zbyt mały, maksymalna częstotliwość z jaką może pracować czujnik to 100kHz")
            return
        value = (1 << 12) | (fref_divider & 0x190)
        self.bus.write_word_data(self.address, CLOCK_DIVIDERS_CH1, value)

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
        self.bus.write_word_data(self.address, DRIVE_CURRENT_CH1, value)

    def set_settling_count(self, count: int = BŁĄD):
        """ustawienie minimalnego czasu ustalania dla czujnika
!!! NIE WIADOMO CO SIE DZIEJE< ODNIESC SIE DO DATASHEETA !!!
        Args:
            count (int, optional): ilość cykli do zliczenia, dla rozdzielczości 28 bitów, minimalna wartość to 1074. Defaults to 0x0500.
        """
        self.bus.write_word_data(self.address, SETTLECOUNT_CH1, count)

    def set_conversion_time(self, rcount: int = 432):
        """ustawienie licznika referencyjnego dla określonego kanału.

        Args:
            rcount (int, optional): _description_. Defaults to 0x0500.
        """
        self.bus.write_word_data(self.address, RCOUNT_CH1, rcount)

    def read_capacitance(self, channel):
        """Read the capacitance value from a specific channel."""
        raw_data = self._read_register(0x00 + 2 * channel)
        return self.calculate_capacitance(raw_data, channel)

    def calculate_capacitance(self, raw_data, channel):
        """Convert raw data into capacitance (placeholder implementation)."""
        # Use the formula from the datasheet to convert raw data to capacitance
        # Example: For FDC2212/FDC2214, capacitance is proportional to raw_data
        return raw_data * 1e-15  # Placeholder conversion to fF

    def read_raw_data(self, channel):
        """Read raw data from a specific channel."""
        return self._read_register(0x00 + 2 * channel)

    def read_all_channels(self):
        """Read capacitance values from all active channels."""
        channels = 4  # Assume 4 channels for FDC2214
        results = {}
        for channel in range(channels):
            results[f"channel_{channel}"] = self.read_capacitance(channel)
        return results

    def check_data_ready(self):
        """Check if new data is ready for any channel."""
        status = self._read_register(0x18)
        return (status & 0x40) != 0

    def read_status(self):
        """Read the status register and return a dictionary of status flags."""
        status = self._read_register(0x18)
        return {
            "data_ready": (status & 0x40) != 0,
            "watchdog_timeout": (status & 0x08) != 0,
            "amplitude_warning": (status & 0x04) != 0,
        }

    def sleep(self):
        """Put the device into sleep mode."""
        config = self._read_register(0x1A)
        self._write_register(0x1A, config | 0x2000)  # Set SLEEP_MODE_EN
        print("Device in sleep mode")

    def wake_up(self):
        """Wake the device from sleep mode."""
        config = self._read_register(0x1A)
        self._write_register(0x1A, config & ~0x2000)  # Clear SLEEP_MODE_EN
        print("Device woken up")

    def shutdown(self):
        """Put the device into shutdown mode."""
        # Use the SD pin if connected, or implement via software if possible
        print("Device shutdown not implemented in software")

    def reset(self):
        """Perform a software reset of the device."""
        self._write_register(0x1C, 0x8000)  # Set RESET_DEV bit
        print("Device reset")

    def clear_errors(self):
        """Clear all error flags in the status register."""
        self._read_register(0x18)  # Reading the status register clears flags

    def get_error_status(self):
        """Retrieve the current error status."""
        status = self._read_register(0x18)
        return {
            "watchdog_timeout": (status & 0x08) != 0,
            "amplitude_warning": (status & 0x04) != 0,
        }

    def set_interrupt_configuration(self, config):
        """Configure the device to trigger interrupts on specific events."""
        error_config = self._read_register(0x19)
        error_config = (error_config & ~0x000F) | (config & 0x000F)
        self._write_register(0x19, error_config)

    def read_manufacturer_id(self):
        """Read the manufacturer ID register."""
        return self._read_register(0x7E)

    def read_device_id(self):
        """Read the device ID register."""
        return self._read_register(0x7F)

    def validate_configuration(self):
        """Validate the current device configuration."""
        # Check if configuration registers are set correctly
        config = self._read_register(0x1A)
        mux_config = self._read_register(0x1B)
        return (config & 0x2801) == 0x2801 and (mux_config & 0xC20D) == 0xC20D

def init():
    bus = SMBus(BUS)
    # kolejność konfiguracji według datasheetu
    bus.write_word_data(ADDR, RCOUNT_CH1, 0xFFFF) # nie jestem pewien co to robi
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