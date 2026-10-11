import json
from pathlib import Path
import numpy as np
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Load telemetry data from local JSON file
DATA_FILE = Path(__file__).resolve().parent / "q-vercel-latency.json"
if not DATA_FILE.exists():
    DATA_FILE = Path(__file__).resolve().parent.parent / "q-vercel-latency.json"

with open(DATA_FILE, "r", encoding="utf-8") as f:
    TELEMETRY_DATA = json.load(f)

@app.get("/")
def root():
    return {"status": "ok"}

@app.options("/")
@app.options("/api/latency")
async def options_handler():
    return Response(status_code=200)

@app.post("/")
@app.post("/api/latency")
async def latency_analytics(request: Request):
    body = await request.json()
    regions = body.get("regions", [])
    threshold_ms = body.get("threshold_ms", 180)

    results = []
    for region in regions:
        records = [r for r in TELEMETRY_DATA if r["region"] == region]
        latencies = [r["latency_ms"] for r in records]
        uptimes = [r["uptime_pct"] for r in records]

        if latencies:
            avg_latency = round(float(np.mean(latencies)), 2)
            p95_latency = round(float(np.percentile(latencies, 95)), 2)
            avg_uptime = round(float(np.mean(uptimes)), 3)
            breaches = int(sum(1 for l in latencies if l > threshold_ms))
        else:
            avg_latency = 0.0
            p95_latency = 0.0
            avg_uptime = 0.0
            breaches = 0

        results.append({
            "region": region,
            "avg_latency": avg_latency,
            "p95_latency": p95_latency,
            "avg_uptime": avg_uptime,
            "breaches": breaches,
        })

    return {"regions": results}