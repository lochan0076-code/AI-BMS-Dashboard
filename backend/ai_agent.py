import os
import time
from google import genai

SYSTEM_PROMPT = """You are the BMS AI Agent — an intelligent Battery Management System assistant connected directly to live hardware sensors.

Your capabilities:
- Read live sensor data (temperature, humidity, voltage, current, battery SOC, RUL)
- Monitor safety sensors (smoke, spark, flame, fire detectors)
- Report battery state of charge, thermal status, and life remaining

Rules:
- Always respond helpfully and concisely (under 3 sentences unless explaining something complex).
- When asked about battery lifespan or remaining useful life (RUL), explicitly quote the value in Days from the live context and explain the impact of current temperature/voltage.
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
- Estimated RUL (Hours): {live_data.get('rul', 'N/A')}
- Predicted RUL (Days): {live_data.get('predicted_rul', 'N/A')}

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

    # Retry loop with fallback models to prevent 503 UNAVAILABLE errors
    models_to_try = ['gemini-1.5-flash', 'gemini-1.5-pro']
    
    for model_name in models_to_try:
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )
                return response.text.strip()
            except Exception as e:
                err_str = str(e)
                if "503" in err_str or "UNAVAILABLE" in err_str:
                    time.sleep(1)
                    continue
                break

    return "The AI service is currently experiencing high demand. Please try again in a few moments."