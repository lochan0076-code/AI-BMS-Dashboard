from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from backend.pi_mock import get_sensor_data, toggle_device, FALLBACK_BMS_DATA
from backend.ai_agent import ask_agent

app = FastAPI()

bms_data = FALLBACK_BMS_DATA

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/")
def root():
    return {"status": "BMS AI Backend Running ✅"}

@app.get("/data")
def data():
    return get_sensor_data()

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
    return {"reply": ask_agent(body["message"])}

@app.post("/control/ejection")
async def control_ejection(request: Request):
    data = await request.json()
    state = data.get('state', 'LOCKED')
    bms_data['ejection_status'] = state
    return {"status": "success", "ejection_status": state}