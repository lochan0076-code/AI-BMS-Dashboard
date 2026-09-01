from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.pi_mock import get_sensor_data, toggle_device
from backend.ai_agent import ask_agent
from datetime import datetime

app = FastAPI(title="AI BMS Dashboard API")

# Global in-memory storage for live hardware data & historical logs
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
    return {"status": "AI BMS Backend Running"}


@app.get("/data")
def data():
    # Return live Raspberry Pi hardware data if available; fallback to mock data
    if latest_hardware_data:
        return latest_hardware_data
    return get_sensor_data()


@app.post("/update_sensor_data")
def update_sensor_data(data: dict):
    global latest_hardware_data, telemetry_logs
    latest_hardware_data = data
    
    # Extract values for the datasheet log table
    voltage = data.get("voltage", 0)
    temperature = data.get("temperature", 0)
    devices = data.get("devices", {})
    fan_status = devices.get("fan", {}).get("status", False)
    light_status = devices.get("light", {}).get("status", False)
    needs_maintenance = data.get("needs_maintenance", False)

    # Format log entry
    log_entry = {
        "timestamp": datetime.now().strftime("%I:%M:%S %p"),
        "voltage": voltage,
        "temperature": temperature,
        "fan": fan_status,
        "light": light_status,
        "maintenance": "MAINTENANCE_REQUIRED" if needs_maintenance else "NORMAL"
    }

    # Keep latest 100 entries for datasheet view
    telemetry_logs.insert(0, log_entry)
    if len(telemetry_logs) > 100:
        telemetry_logs.pop()

    return {"status": "success"}


@app.get("/logs")
def get_logs():
    return telemetry_logs


@app.post("/toggle/{device}")
def toggle(device: str):
    result = toggle_device(device.lower())

    if result is None:
        return {"error": f"Device '{device}' not found"}

    return result

@app.post("/chat")
def chat(body: dict):
    message = body.get("message", "")

    if not message:
        return {"reply": "Please provide a valid message."}

    return {"reply": ask_agent(message)}

@app.post("/control/ejection")
async def control_ejection(request: Request):
    data = await request.json()
    state = data.get('state', 'LOCKED')
    return {"status": "success", "ejection_status": state}