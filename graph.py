import json
import os
import networkx as nx
from collector import discover_topology

TOPOLOGY_FILE = "data/topology.json"

def build_and_save() -> dict:
    edges = discover_topology()
    G = nx.Graph()
    for e in edges:
        G.add_node(e["local"])
        G.add_node(e["remote"], ip=e["ip"], platform=e["platform"])
        G.add_edge(e["local"], e["remote"],
                   local_port=e["local_port"],
                   remote_port=e["remote_port"])

    data = {
        "nodes": [{"id": n, "label": n, **G.nodes[n]} for n in G.nodes],
        "edges": [
            {"source": u, "target": v,
             "local_port": d.get("local_port",""),
             "remote_port": d.get("remote_port","")}
            for u, v, d in G.edges(data=True)
        ]
    }
    os.makedirs("data", exist_ok=True)
    with open(TOPOLOGY_FILE, "w") as f:
        json.dump(data, f, indent=2)
    print(f"[OK] {len(data['nodes'])} nodes, {len(data['edges'])} edges saved.")
    return data

if __name__ == "__main__":
    build_and_save()