from groq import Groq
import json
from pi_mock import get_sensor_data, toggle_device, calculate_bill

client = Groq(api_key="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")

SYSTEM = """You are a smart home AI assistant controlling a Raspberry Pi dashboard.
You help the user control devices (fan, light, ac), read sensor data, and calculate electricity bills.
Reply concisely and clearly."""

def ask_agent(user_msg: str) -> str:
    state = json.dumps(get_sensor_data(), indent=2)
    bill  = json.dumps(calculate_bill(), indent=2)
    context = f"Current sensor state:\n{state}\nCurrent bill (24h):\n{bill}"

    for device in ["fan", "light", "ac"]:
        if device in user_msg.lower():
            if any(w in user_msg.lower() for w in ["on","off","toggle","turn"]):
                result = toggle_device(device)
                status = "ON" if result["status"] else "OFF"
                return f"{device.capitalize()} is now {status}."

    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[
            {"role": "system", "content": SYSTEM + "\n" + context},
            {"role": "user",   "content": user_msg}
        ]
    )
    return response.choices[0].message.content