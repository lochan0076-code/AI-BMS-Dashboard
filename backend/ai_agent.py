import json
import os
import google.generativeai as genai
from dotenv import load_dotenv
from backend.pi_mock import get_sensor_data, toggle_device, calculate_billx
load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

SYSTEM = """You are BMS AI Agent — an intelligent Battery Management System assistant 
controlling a smart home dashboard connected to a Raspberry Pi 3B+.

Your capabilities:
- Read live sensor data (temperature, humidity, voltage, current, power, battery SOC)
- Monitor safety sensors (smoke, spark, flame, fire detectors)
- Toggle the BMS device ON or OFF
- Monitor device status (fan and light are read-only — cannot be controlled)
- Calculate electricity bills in Indian Rupees (₹) at ₹8/kWh (Karnataka BESCOM tariff)
- Alert users urgently about fire, smoke or spark hazards
- Report battery state of charge (SOC) and battery status

Rules:
- Always respond helpfully and concisely (under 3 sentences unless explaining something)
- When fire/smoke/spark is detected, respond with URGENT warnings
- Use ₹ symbol for all currency values
- Fan and light cannot be toggled — only BMS device can be toggled
- Always confirm actions taken on BMS device
"""

def ask_agent(user_msg: str) -> str:
    try:
        state = get_sensor_data()
        bill  = calculate_bill()

        context = f"""
Live BMS Sensor Data:
- Temperature: {state['temperature']}°C
- Humidity: {state['humidity']}%
- Voltage: {state['voltage']}V
- Current: {state['current']}A
- Power: {state['power']}W
- Battery SOC: {state.get('battery_soc', 'N/A')}%
- Battery Status: {state.get('battery_status', 'N/A')}

Safety Status:
- Smoke: {'DETECTED ⚠️' if state['safety']['smoke'] else 'Clear'}
- Spark: {'DETECTED ⚠️' if state['safety']['spark'] else 'Clear'}
- Flame: {'DETECTED ⚠️' if state['safety']['flame'] else 'Clear'}
- Fire:  {'🔥 CRITICAL' if state['safety']['fire'] else 'Clear'}
- Alerts: {', '.join(state['alerts']) if state['alerts'] else 'None'}

Device Status:
- Fan: {'ON' if state['devices']['fan']['status'] else 'OFF'} (50W, read-only)
- Light: {'ON' if state['devices']['light']['status'] else 'OFF'} (10W, read-only)
- BMS Device: {'ON' if state['devices']['bms']['status'] else 'OFF'} (5W, controllable)

Electricity Bill (24h): ₹{bill['bill_inr']} ({bill['kwh']} kWh)
"""

        # Handle BMS toggle commands
        msg_lower = user_msg.lower()
        if "bms" in msg_lower:
            if any(w in msg_lower for w in ["on","off","toggle","turn","start","stop","enable","disable"]):
                result = toggle_device("bms")
                if result:
                    status = "ON" if result["status"] else "OFF"
                    return f"✅ BMS Device has been turned {status}."

        # Handle fan/light toggle attempts
        if any(d in msg_lower for d in ["fan","light"]):
            if any(w in msg_lower for w in ["on","off","toggle","turn"]):
                return "⚠️ Fan and Light are monitoring-only devices. Only the BMS Device can be toggled from this dashboard."

        # Build full prompt
        prompt = f"{SYSTEM}\n\nCurrent Context:\n{context}\n\nUser: {user_msg}\n\nBMS AI Agent:"

        response = model.generate_content(prompt)
        return response.text.strip()

    except Exception as e:
        return f"BMS Agent error: {str(e)}"