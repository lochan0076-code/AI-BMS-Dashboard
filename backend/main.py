from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.pi_mock import get_sensor_data, toggle_device, calculate_bill
from backend.ai_agent import ask_agent

app = FastAPI(title="AI BMS Dashboard API")


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
    return get_sensor_data()


@app.post("/toggle/{device}")
def toggle(device: str):
    result = toggle_device(device.lower())

    if result is None:
        return {"error": f"Device '{device}' not found"}

    return result


@app.get("/bill")
def bill(hours: float = 24.0):
    return calculate_bill(hours)


@app.post("/chat")
def chat(body: dict):
    message = body.get("message", "")

    if not message:
        return {"reply": "Please provide a valid message."}

    return {"reply": ask_agent(message)}