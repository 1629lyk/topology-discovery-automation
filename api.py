import json
import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from graph import build_and_save

app = FastAPI(title="Network Topology API", version="1.0.0")
app.mount("/static", StaticFiles(directory="static"), name="static")

TOPOLOGY_FILE = "data/topology.json"

@app.get("/")
def root():
    return FileResponse("static/topology.html")

@app.get("/api/topology")
def get_topology():
    if not os.path.exists(TOPOLOGY_FILE):
        raise HTTPException(status_code=404, detail="No topology yet. POST /api/discover first.")
    with open(TOPOLOGY_FILE) as f:
        return json.load(f)

@app.post("/api/discover")
def discover():
    try:
        data = build_and_save()
        return {"status": "ok", "nodes": len(data["nodes"]), "edges": len(data["edges"])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/nodes/{node_id}")
def get_node(node_id: str):
    if not os.path.exists(TOPOLOGY_FILE):
        raise HTTPException(status_code=404, detail="No topology yet.")
    with open(TOPOLOGY_FILE) as f:
        data = json.load(f)
    node = next((n for n in data["nodes"] if n["id"] == node_id), None)
    if not node:
        raise HTTPException(status_code=404, detail=f"Node '{node_id}' not found.")
    neighbors = [
        e["target"] if e["source"] == node_id else e["source"]
        for e in data["edges"]
        if node_id in (e["source"], e["target"])
    ]
    return {**node, "neighbors": neighbors}