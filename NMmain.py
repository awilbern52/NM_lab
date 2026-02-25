import NMdhcp, NMgithub, NMsnmp, NMtcpdump

def main():
    print("starting tcpdump analysis...")
    NMtcpdump.main()
    
    print("starting dhcp configuration...")
    NMdhcp.main()

    print("starting snmp monitoring...")
    NMsnmp.main()

    print("pushing to github...")
    NMgithub.main()

    print("lab5 complete.")


if __name__ == "__main__":
    main()