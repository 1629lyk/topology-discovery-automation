import yaml
import re
from netmiko import ConnectHandler

def load_inventory(path="inventory.yaml"):
    with open(path) as f:
        return yaml.safe_load(f)["devices"]

def get_cdp_neighbors(device: dict) -> list:
    conn_params = {
        "device_type": device["device_type"],
        "host": device["host"],
        "username": device["username"],
        "password": device["password"],
    }
    try:
        with ConnectHandler(**conn_params) as conn:
            output = conn.send_command("show cdp neighbors detail")
            return parse_cdp(output, device["hostname"])
    except Exception as e:
        print(f"[WARN] {device['hostname']}: {e}")
        return []

def parse_cdp(output: str, local: str) -> list:
    entries = re.split(r"-{5,}", output)
    neighbors = []
    for entry in entries:
        remote = re.search(r"Device ID:\s*(\S+)", entry)
        ports = re.search(r"Interface:\s*(\S+),\s*Port ID[^:]*:\s*(\S+)", entry)
        ip = re.search(r"IP address:\s*(\S+)", entry)
        plat = re.search(r"Platform:\s*([^,]+)", entry)
        if remote and ports:
            neighbors.append({
                "local": local,
                "local_port": ports.group(1).rstrip(","),
                "remote": remote.group(1).split(".")[0],
                "remote_port": ports.group(2),
                "ip": ip.group(1) if ip else "unknown",
                "platform": plat.group(1).strip() if plat else "unknown",
            })
    return neighbors

def discover_topology(inventory_path="inventory.yaml") -> list:
    devices = load_inventory(inventory_path)
    all_edges = []
    seen = set()
    visited = set()
    queue = list(devices)

    # seed known IPs from inventory
    ip_map = {d["hostname"]: d["host"] for d in devices}

    while queue:
        device = queue.pop(0)
        if device["hostname"] in visited:
            continue
        visited.add(device["hostname"])
        print(f"[INFO] Scanning {device['hostname']} ({device['host']})")
        neighbors = get_cdp_neighbors(device)

        for n in neighbors:
            pair = tuple(sorted([n["local"], n["remote"]]))
            if pair not in seen:
                seen.add(pair)
                all_edges.append(n)
            # if neighbor has an IP and not yet visited, queue it
            if n["ip"] != "unknown" and n["remote"] not in visited:
                queue.append({
                    "hostname": n["remote"],
                    "host": n["ip"],
                    "device_type": device["device_type"],
                    "username": device["username"],
                    "password": device["password"],
                })

    return all_edges

if __name__ == "__main__":
    edges = discover_topology()
    print(f"\nDiscovered {len(edges)} links:")
    for e in edges:
        print(f"{e['local']} {e['local_port']} <--> {e['remote']} {e['remote_port']}")