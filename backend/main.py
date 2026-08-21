from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from backend.pi_mock import generate_telemetry, toggle_device, _find_bms_data_path
import json

app = FastAPI()

# Global in-memory list to store telemetry log history
telemetry_logs = []

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

def get_sensor_data():
    """Reads telemetry from bms_data.json or falls back to live generated data."""
    json_path = _find_bms_data_path()
    if json_path:
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return generate_telemetry()

@app.get("/")
def root():
    return {"status": "BMS AI Backend Running ✅"}

@app.get("/data")
def data():
    sensor_data = get_sensor_data()
    
    # Extract values for the log table
    voltage = sensor_data.get("voltage", 0)
    temperature = sensor_data.get("temperature", 0)
    
    devices = sensor_data.get("devices", {})
    fan_status = devices.get("fan", {}).get("status", False)
    light_status = devices.get("light", {}).get("status", False)
    needs_maintenance = sensor_data.get("needs_maintenance", False)
    
    # Format log entry
    log_entry = {
        "timestamp": datetime.now().strftime("%I:%M:%S %p"),
        "voltage": voltage,
        "temperature": temperature,
        "fan": fan_status,
        "light": light_status,
        "maintenance": "MAINTENANCE_REQUIRED" if needs_maintenance else "NORMAL"
    }
    
    # Keep latest 100 entries
    telemetry_logs.insert(0, log_entry)
    if len(telemetry_logs) > 100:
        telemetry_logs.pop()
        
    return sensor_data

@app.get("/logs")
def get_logs():
    """Returns historical telemetry logs for the frontend datasheet modal."""
    return telemetry_logs

@app.post("/toggle/{device}")
def toggle(device: str):
    if device.lower() != "bms":
        return {"error": "Only BMS device can be toggled"}
    result = toggle_device(device)
    if result is None:
        return {"error": "Toggle failed"}
    return result

@app.post("/chat")
def chat(body: dict):
    # Place holder if ai_agent is imported separately
    from backend.ai_agent import ask_agent
    return {"reply": ask_agent(body["message"])}

@app.post("/control/ejection")
async def control_ejection(request: Request):
    data = await request.json()
    state = data.get('state', 'LOCKED')
    return {"status": "success", "ejection_status": state}