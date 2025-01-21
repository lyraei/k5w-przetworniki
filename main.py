from devices import AD7745  # FDC2212 ,AD7745 ,PCAP04
from time import sleep

# texas = FDC2212.FDC2212()
# texas.initialize()

analog = AD7745.AD7745()
analog.initialize()

# pcap = PCAP04.PCAP04()
# pcap.initialize()

def main():
    analog.initialize()
    while True:
        print(analog.read_capacitance())
        sleep(1e-2)
    
    # for i in range(0, 0x2A):
        # sleep(0.1)
        # print("PCAP04: Reg " + str(hex(i)), bin(pcap.read_capacitance(i)))
        
        
main()