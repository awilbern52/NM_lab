import NMdhcp, NMgithub, NMsnmp, NMtcpdump

def main():
    print("\nstarting tcpdump analysis...")
    NMtcpdump.main()
    
    print("\nstarting dhcp configuration...")
    NMdhcp.main()

    print("\nstarting snmp monitoring...")
    NMsnmp.main()

    print("\npushing to github...")
    NMgithub.main()

    print("\nlab5 complete.\n")


if __name__ == "__main__":
    main()