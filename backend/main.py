from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, List

app = FastAPI(title="AI BMS Dashboard API")

latest_hardware_data = {}
telemetry_logs = []

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "AI BMS Backend Running"}

@app.post("/update_sensor_data")
def update_sensor_data(data: dict):
    global latest_hardware_data, telemetry_logs
    latest_hardware_data = data
    telemetry_logs.append(data)
    if len(telemetry_logs) > 100:
        telemetry_logs.pop(0)
    return {"status": "success", "received": data}

@app.get("/data")
def get_data():
    if not latest_hardware_data:
        return {
            "voltage": 0.0,
            "current": 0.0,
            "temperature": 0.0,
            "soc": 0,
            "soh": 100,
            "rul": "N/A",
            "alerts": []
        }
    return latest_hardware_data
