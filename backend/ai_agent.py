import os
from google import genai

SYSTEM_PROMPT = """You are the BMS AI Agent — an intelligent Battery Management System assistant connected directly to live hardware sensors.

Your capabilities:
- Read live sensor data (temperature, humidity, voltage, current, battery SOC, RUL)
- Monitor safety sensors (smoke, spark, flame, fire detectors)
- Report battery state of charge, thermal status, and life remaining

Rules:
- Always respond helpfully and concisely (under 3 sentences unless explaining something complex).
- When fire, smoke, or spark is detected, respond with URGENT warnings.
- Always confirm status clearly.
"""

def ask_agent(user_msg: str, live_data: dict) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "AI Agent offline: GEMINI_API_KEY is not set in Render environment variables."

    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        return f"AI Agent error initializing client: {str(e)}"

    safety = live_data.get('safety', {})
    devices = live_data.get('devices', {})

    context = f"""
Live BMS Hardware Data:
- Temperature: {live_data.get('temperature', 0.0)}°C
- Humidity: {live_data.get('humidity', 0.0)}%
- Voltage: {live_data.get('voltage', 0.0)}V
- Current: {live_data.get('current', 0.0)}A
- Battery SOC: {live_data.get('soc', 'N/A')}%
- Remaining Useful Life (RUL): {live_data.get('rul', 'N/A')}

Safety Status:
- Smoke: {'DETECTED ⚠️' if safety.get('smoke') else 'Clear'}
- Spark / Flame: {'DETECTED ⚠️' if safety.get('spark') or safety.get('flame') else 'Clear'}
- Fire: {'🔥 CRITICAL' if safety.get('fire') else 'Clear'}

Device Status:
- Fan: {'ON' if devices.get('fan', {}).get('status') else 'OFF'}
- Light: {'ON' if devices.get('light', {}).get('status') else 'OFF'}
- Maintenance Required: {'YES' if live_data.get('needs_maintenance') else 'NO'}
"""
    prompt = f"{SYSTEM_PROMPT}\n\nCurrent Context:\n{context}\n\nUser Question: {user_msg}\n\nBMS AI Agent:"

    try:
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=prompt,
        )
        return response.text.strip()
    except Exception as e:
        return f"BMS Agent error: {str(e)}"