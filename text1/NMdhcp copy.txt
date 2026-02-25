from napalm import get_network_driver
import os, yaml, re

router_config = "lab5routers.yaml"

r2_mac = "ca02.31b1.0000"
r3_mac = "ca03.31c0.0000"

dhcp_network = "10.12.0.0"
dhcp_mask = "255.255.255.0"
default_gateway = "10.12.0.1"

def load_routers():
    if not os.path.isfile(router_config):
        raise FileNotFoundError(f"{router_config} not found.")
    
    with open(router_config, 'r') as file:
        data = yaml.safe_load(file)
    
    if "routers" not in data:
        raise KeyError("'routers' key not found in routers.yaml")
    
    return data["routers"]

def connect_device(router):
    driver = get_network_driver(router["platform"])
    device = driver(
        hostname=router["hostname"],
        username=router["username"],
        password=router["password"],
    )
    device.open()
    return device

def mac_to_cisco_client_id(mac):
    # remove any separators except dots
    mac = mac.lower()

    # build ascii string used by cisco routers
    ascii_id = f"cisco-{mac}-Fa0/0"

    # convert ascii string to hex
    hex_string = ascii_id.encode().hex()

    # format into cisco dotted style (4 hex chars per group)
    dotted = ".".join(hex_string[i:i+4] for i in range(0, len(hex_string), 4))

    # prepend leading 00 (as seen in your binding table)
    return f"00{dotted}"

r2_client_id = mac_to_cisco_client_id(r2_mac)
r3_client_id = mac_to_cisco_client_id(r3_mac)

def get_r5_ipv6_from_r4(r4_device):
    output = r4_device.cli(["show ipv6 neighbors"])["show ipv6 neighbors"]

    for line in output.splitlines():
        parts = line.split()
        if not parts:
            continue

        ipv6 = parts[0]

        # ignore link-local
        if ipv6.lower().startswith("fe80"):
            continue

        # only match r5 network (BEEF::)
        if ipv6.lower().startswith("beef"):
            return parts[0]

    raise Exception("could not determine r5 ipv6 in BEEF:: network")


def configure_dhcp_on_r5(r5_device):
    config_commands = f"""
    interface f0/0
    ip address {default_gateway} {dhcp_mask}
    no shutdown
    exit

    ip dhcp excluded-address {default_gateway} 10.12.0.20

    ip dhcp pool R2_HOST
    host 10.12.0.12 255.255.255.0
    client-identifier {r2_client_id}
    default-router {default_gateway}

    ip dhcp pool R3_HOST
    host 10.12.0.13 255.255.255.0
    client-identifier {r3_client_id}
    default-router {default_gateway}

    ip dhcp pool R4_DYNAMIC
    network {dhcp_network} {dhcp_mask}
    default-router {default_gateway}
    """

    r5_device.load_merge_candidate(config=config_commands)
    r5_device.commit_config()

    output = r5_device.cli(["show ip dhcp binding"])
    return output["show ip dhcp binding"]

def parse_bindings(binding_output):
    ips = re.findall(r"\d+\.\d+\.\d+\.\d+", binding_output)
    return ips


def main():
    routers = load_routers()

    # connect to r4
    r4 = connect_device(routers["R4"])

    # discover r5 ipv6
    r5_ipv6 = get_r5_ipv6_from_r4(r4)
    r4.close()

    # dynamically set r5 hostname to ipv6
    routers["R5"]["hostname"] = r5_ipv6

    # connect to r5
    r5 = connect_device(routers["R5"])

    bindings_output = configure_dhcp_on_r5(r5)
    r5.close()

    client_ips = parse_bindings(bindings_output)

    print("dhcpv4 clients:")
    for ip in client_ips:
        print(ip)


if __name__ == "__main__":
    main()