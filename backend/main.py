from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from datetime import datetime
import os

try:
    from backend.ai_agent import ask_agent
except ImportError:
    ask_agent = None

def calculate_rul(voltage, temperature):
    base_rul_hours = 1200
    temp_penalty = max(0, (temperature - 25) * 15)
    volt_penalty = max(0, (48.0 - voltage) * 20)
    estimated_rul_hours = max(0, int(base_rul_hours - temp_penalty - volt_penalty))
    return f"{estimated_rul_hours} Hours"

def calculate_predicted_rul(voltage, temperature):
    base_rul_hours = 1200
    temp_penalty = max(0, (temperature - 25) * 15)
    volt_penalty = max(0, (48.0 - voltage) * 20)
    estimated_rul_hours = max(0, int(base_rul_hours - temp_penalty - volt_penalty))
    estimated_rul_days = round(estimated_rul_hours / 24, 1)
    return f"{estimated_rul_days} Days"

app = FastAPI(title="AI BMS Dashboard API")

app.mount("/static", StaticFiles(directory="."), name="static")

latest_hardware_data = {}
telemetry_logs = []

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return FileResponse("index.html")

@app.get("/data")
def data():
    if not latest_hardware_data:
        return {
            "temperature": 0.0,
            "humidity": 0.0,
            "voltage": 0.0,
            "current": 0.0,
            "soc": 0.0,
            "soh": 0.0,
            "rul": "0",
            "predicted_rul": "0 Days",
            "needs_maintenance": False,
            "devices": {"fan": {"status": False}, "light": {"status": False}, "bms": {"status": False}},
            "safety": {"smoke": False, "spark": False, "fire": False}
        }
    
    d = dict(latest_hardware_data)
    d["rul"] = calculate_rul(d.get("voltage", 0.0), d.get("temperature", 0.0))
    d["predicted_rul"] = calculate_predicted_rul(d.get("voltage", 0.0), d.get("temperature", 0.0))
    return d

@app.post("/update_sensor_data")
def update_sensor_data(data: dict):
    global latest_hardware_data, telemetry_logs
    latest_hardware_data = data
    
    voltage = data.get("voltage", 0)
    temperature = data.get("temperature", 0)
    devices = data.get("devices", {})
    fan_status = devices.get("fan", {}).get("status", False)
    light_status = devices.get("light", {}).get("status", False)
    needs_maintenance = data.get("needs_maintenance", False)

    log_entry = {
        "timestamp": datetime.now().strftime("%I:%M:%S %p"),
        "voltage": voltage,
        "temperature": temperature,
        "fan": fan_status,
        "light": light_status,
        "maintenance": "MAINTENANCE_REQUIRED" if needs_maintenance else "NORMAL"
    }

    telemetry_logs.insert(0, log_entry)
    if len(telemetry_logs) > 100:
        telemetry_logs.pop()

    return {"status": "success"}

@app.get("/logs")
def get_logs():
    return telemetry_logs

@app.post("/toggle/{device}")
def toggle(device: str):
    return {"status": "success", "device": device}

@app.post("/chat")
def chat(body: dict):
    message = body.get("message", "")
    if not message:
        return {"reply": "Please provide a valid message."}
    if ask_agent:
        payload = dict(latest_hardware_data)
        payload["rul"] = calculate_rul(payload.get("voltage", 0.0), payload.get("temperature", 0.0))
        payload["predicted_rul"] = calculate_predicted_rul(payload.get("voltage", 0.0), payload.get("temperature", 0.0))
        return {"reply": ask_agent(message, payload)}
    return {"reply": "AI Agent offline."}

@app.post("/control/ejection")
async def control_ejection(request: Request):
    data = await request.json()
    state = data.get('state', 'LOCKED')
    return {"status": "success", "ejection_status": state}