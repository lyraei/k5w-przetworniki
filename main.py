from devices import AD7745, FDC2212, PCAP04
from time import sleep

teaxs = FDC2212.FDC2212()
teaxs.initialize()

analog = AD7745.AD7745()
analog.initialize()

pcap = PCAP04.PCAP04()
pcap.initialize()

def main():
    while True:
        sleep(1)
        print("FDC2212: C_sens = " + str(teaxs.read_capacitance()) + "[F]")
    
    
main()