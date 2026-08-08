from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pi_mock import get_sensor_data, toggle_device, calculate_bill
from ai_agent import ask_agent

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/")
def root():
    return {"status": "AI BMS Backend Running"}

@app.get("/data")
def data():
    return get_sensor_data()

@app.post("/toggle/{device}")
def toggle(device: str):
    result = toggle_device(device)
    if result is None:
        return {"error": "Device not found"}
    return result

@app.get("/bill")
def bill(hours: float = 24):
    return calculate_bill(hours)

@app.post("/chat")
def chat(body: dict):
    return {"reply": ask_agent(body["message"])}