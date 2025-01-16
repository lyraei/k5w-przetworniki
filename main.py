from devices import PCAP04  # FDC2212 ,AD7745 ,PCAP04
from time import sleep

# texas = FDC2212.FDC2212()
# texas.initialize()

# analog = AD7745.AD7745()
# analog.initialize()

pcap = PCAP04.PCAP04()
pcap.initialize()

# def main():
    # pcap.test()
    # for i in range(0, 0x2A):
        # sleep(0.1)
        # print("PCAP04: Reg " + str(hex(i)), bin(pcap.read_capacitance(i)))
        
        
# main()