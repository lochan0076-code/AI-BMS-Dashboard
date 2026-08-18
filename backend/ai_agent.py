import os
from google import genai
from backend.pi_mock import get_sensor_data, toggle_device

# Initializes Google GenAI client using the GOOGLE_API_KEY environment variable
client = genai.Client()

SYSTEM_PROMPT = """You are the BMS AI Agent — an intelligent Battery Management System assistant 
connected to a Raspberry Pi 3B+.

Your capabilities:
- Read live sensor data (temperature, humidity, voltage, current, power, battery SOC)
- Monitor safety sensors (smoke, spark, flame, fire detectors)
- Trigger the Battery Ejection System in emergency scenarios
- Report battery state of charge (SOC) and thermal status

Rules:
- Always respond helpfully and concisely (under 3 sentences unless explaining something complex)
- When fire, smoke, or spark is detected, respond with URGENT warnings and suggest ejecting the battery module if unsafe
- Always confirm status changes clearly
"""

def ask_agent(user_msg: str) -> str:
    try:
        state = get_sensor_data()

        context = f"""
Live BMS Sensor Data:
- Temperature: {state.get('temperature', 'N/A')}°C
- Humidity: {state.get('humidity', 'N/A')}%
- Voltage: {state.get('voltage', 'N/A')}V
- Current: {state.get('current', 'N/A')}A
- Power: {state.get('power', 'N/A')}W
- Battery SOC: {state.get('battery_soc', 'N/A')}%
- Battery Status: {state.get('battery_status', 'N/A')}

Safety Status:
- Smoke: {'DETECTED ⚠️' if state.get('safety', {}).get('smoke') else 'Clear'}
- Spark: {'DETECTED ⚠️' if state.get('safety', {}).get('spark') else 'Clear'}
- Flame: {'DETECTED ⚠️' if state.get('safety', {}).get('flame') else 'Clear'}
- Fire:  {'🔥 CRITICAL' if state.get('safety', {}).get('fire') else 'Clear'}

System Status:
- Battery Ejection System: {state.get('ejection_status', 'LOCKED')}
"""

        msg_lower = user_msg.lower()

        # Handle Battery Ejection commands
        if any(w in msg_lower for w in ["eject", "ejection", "release", "disconnect"]):
            result = toggle_device("ejection")
            if result:
                status = "EJECTED ⚠️" if result.get("status") else "LOCKED"
                return f"🚨 Battery Ejection System status updated: **{status}**."

        # Build full prompt for Gemini 2.5
        prompt = f"{SYSTEM_PROMPT}\n\nCurrent Context:\n{context}\n\nUser Question: {user_msg}\n\nBMS AI Agent:"

        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=prompt,
        )
        return response.text.strip()

    except Exception as e:
        return f"BMS Agent error: {str(e)}"