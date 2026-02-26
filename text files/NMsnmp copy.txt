import json
import time
import ipaddress
import matplotlib.pyplot as plt
from pysnmp.hlapi import *

COMMUNITY = "public"

ROUTERS = {
    "R1": "10.10.0.1",
    "R2": "10.12.0.12",
    "R3": "10.12.0.13",
    "R4": "10.12.0.21",
    "R5": "10.12.0.1",
}

# OIDs
IF_DESCR = '1.3.6.1.2.1.2.2.1.2'
IF_STATUS = '1.3.6.1.2.1.2.2.1.8'
IPV4_ADDR = '1.3.6.1.2.1.4.20.1.1'
IPV4_IFINDEX = '1.3.6.1.2.1.4.20.1.2'
IP_IFINDEX = '1.3.6.1.2.1.4.34.1.3'
CPU_OID = '1.3.6.1.4.1.9.2.1.57.0'


def snmp_walk(ip, oid):
    results = {}
    for (errorIndication, errorStatus, errorIndex, varBinds) in nextCmd(
            SnmpEngine(),
            CommunityData(COMMUNITY, mpModel=1),
            UdpTransportTarget((ip, 161)),
            ContextData(),
            ObjectType(ObjectIdentity(oid)),
            lexicographicMode=False):

        if errorIndication or errorStatus:
            break

        for varBind in varBinds:
            results[str(varBind[0])] = varBind[1].prettyPrint()

    return results


def snmp_get(ip, oid):
    iterator = getCmd(
        SnmpEngine(),
        CommunityData(COMMUNITY, mpModel=1),
        UdpTransportTarget((ip, 161)),
        ContextData(),
        ObjectType(ObjectIdentity(oid))
    )

    errorIndication, errorStatus, errorIndex, varBinds = next(iterator)

    if errorIndication or errorStatus:
        return None

    return int(varBinds[0][1])


def collect_data():
    network_data = {}

    for name, ip in ROUTERS.items():

        interfaces = snmp_walk(ip, IF_DESCR)
        statuses = snmp_walk(ip, IF_STATUS)
        ipv4_addrs = snmp_walk(ip, IPV4_ADDR)
        ipv4_index = snmp_walk(ip, IPV4_IFINDEX)
        ip_table = snmp_walk(ip, IP_IFINDEX)

        router_info = {
            "addresses": {},
            "interface_status": {}
        }

        # build interface mapping
        index_to_name = {}
        for oid, iface in interfaces.items():
            idx = oid.split('.')[-1]
            index_to_name[idx] = iface
            router_info["addresses"][iface] = {"v4": [], "v6": []}

        # interface status
        for oid, status in statuses.items():
            idx = oid.split('.')[-1]
            if idx in index_to_name:
                router_info["interface_status"][index_to_name[idx]] = (
                    "up" if status == "1" else "down"
                )

        # map ipv4
        for oid, addr in ipv4_addrs.items():
            idx_oid = oid.replace(IPV4_ADDR, IPV4_IFINDEX)
            if idx_oid in ipv4_index:
                iface_idx = ipv4_index[idx_oid]
                if iface_idx in index_to_name:
                    router_info["addresses"][index_to_name[iface_idx]]["v4"].append(addr)

        # map ipv6 (extracted from OID index)
        for oid, iface_idx in ip_table.items():

            parts = oid.split('.')
            base_len = len(IP_IFINDEX.split('.'))

            addr_type = int(parts[base_len])
            addr_len = int(parts[base_len + 1])

            addr_bytes = parts[base_len + 2: base_len + 2 + addr_len]
            addr_bytes = [int(b) for b in addr_bytes]

            if addr_type == 2:  # ipv6
                ipv6_addr = str(ipaddress.IPv6Address(bytes(addr_bytes)))

                if iface_idx in index_to_name:
                    router_info["addresses"][index_to_name[iface_idx]]["v6"].append(ipv6_addr)

        network_data[name] = router_info

    return network_data


def poll_cpu():
    timestamps = []
    cpu_values = []

    for i in range(24):  # 2 minutes
        cpu = snmp_get(ROUTERS["R1"], CPU_OID)
        if cpu is not None:
            timestamps.append(i * 5)
            cpu_values.append(cpu)
        time.sleep(5)

    return timestamps, cpu_values


def plot_cpu(timestamps, cpu_values):
    plt.figure()
    plt.plot(timestamps, cpu_values)
    plt.xlabel("Time (seconds)")
    plt.ylabel("CPU Utilization (%)")
    plt.title("R1 CPU Utilization (2 Minutes)")
    plt.savefig("R1_CPU.jpg")


def main():
    data = collect_data()

    with open("snmp_output.txt", "w") as f:
        json.dump(data, f, indent=4)

    timestamps, cpu_values = poll_cpu()
    plot_cpu(timestamps, cpu_values)


if __name__ == "__main__":
    main()