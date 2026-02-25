from scapy.all import rdpcap, Ether, IP

# packets = rdpcap("R4_FastEthernet10_to_Cloud1_tap0.pcap")
# packets = rdpcap("R2_FastEthernet00_to_Switch2_Ethernet0.pcap")
packets = rdpcap("R3_FastEthernet00_to_Switch2_Ethernet1.pcap")

def extract_router_macs(packets):
    router_macs = set()
    for pkt in packets:
        if pkt.haslayer(Ether) and pkt.haslayer(IP) and pkt[IP].proto == 1:
            src_mac = pkt[Ether].src
            # dst_mac = pkt[Ether].dst
            router_macs.add(src_mac)
            # router_macs.add(dst_mac)
    return router_macs

def main():
    router_macs = extract_router_macs(packets)
    print("router MAC addresses found:")
    for mac in router_macs:
        print(mac)

if __name__ == "__main__":
    main()