import os
import json
import random
import time
import requests
from datetime import datetime

def _find_bms_data_path():
    """Find bms_data.json relative to backend file or current working directory."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(base_dir, "..", "bms_data.json"),
        os.path.join(base_dir, "..", "..", "bms_data.json"),
        os.path.join(os.getcwd(), "bms_data.json"),
        os.path.join(os.getcwd(), "AI-BMS-Dashboard", "bms_data.json"),
    ]
    for candidate in candidates:
        if os.path.isfile(candidate):
            return candidate
    return None

    

def generate_telemetry():
    """Generates complete telemetry with dynamic toggles and maintenance health logic."""
    fan_status = random.choice([True, False])
    light_status = random.choice([True, False])
    
    # Live sensor reading simulations
    temp = round(random.uniform(28.0, 44.0), 1)
    voltage = round(random.uniform(42.0, 54.0), 1)
    humidity = round(random.uniform(55.0, 68.0), 1)
    
    # Rule 1: Maintenance required if temp > 40°C or voltage < 44V
    needs_maintenance = (temp > 40.0 or voltage < 44.0)

    # Dynamic safety alerts
    smoke = temp > 50.0
    spark = temp > 60.0 
    flame = spark
    fire = smoke and spark

    alerts = []
    if smoke: alerts.append("Smoke detected")
    if spark or flame: alerts.append("Spark/Flame detected")
    if fire: alerts.append("CRITICAL: Fire Hazard Detected")

    telemetry = {
        "device_id": "AI-BMS-PI3B",
        "timestamp": datetime.now().astimezone().isoformat(),
        "online": True,
        "temperature": temp,
        "humidity": humidity,
        "voltage": voltage,
        "current": round(random.uniform(2.0, 8.0), 2),
        "power": 121.73,
        "battery_soc": random.randint(70, 95),
        "battery_status": "NORMAL" if not needs_maintenance else "MAINTENANCE_REQUIRED",
        "needs_maintenance": needs_maintenance,  # <--- Added for UI light indicator
        "safety": {
            "smoke": smoke,
            "spark": spark,
            "flame": flame,
            "fire": fire
        },
        "devices": {
            "fan": {"status": fan_status, "watts": 50},
            "light": {"status": light_status, "watts": 10},
            "bms": {"status": True, "watts": 5}
        },
        "alerts": alerts,
        "test_mode": False
    }
    return telemetry

def toggle_device(name: str):
    """Toggle BMS status."""
    name = name.lower()
    if name != "bms":
        return None
    
    json_path = _find_bms_data_path() or "bms_data.json"
    try:
        with open(json_path, "r") as f:
            data = json.load(f)
        current = data["devices"]["bms"]["status"]
        data["devices"]["bms"]["status"] = not current
        with open(json_path, "w") as f:
            json.dump(data, f, indent=4)
        return data["devices"]["bms"]
    except Exception as e:
        print(f"Error toggling BMS: {e}")
        return None

# This was changed in 21/08/2026 at 8:28 PM
FALLBACK_BMS_DATA = generate_telemetry()

def get_sensor_data():
    """Returns telemetry generated on demand or read from JSON."""
    json_path = _find_bms_data_path()
    if json_path and os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return generate_telemetry()

if __name__ == "__main__":
    json_path = _find_bms_data_path() or "bms_data.json"
    print(f"Starting BMS telemetry updater... Writing to {json_path}")
    
    while True:
        telemetry = generate_telemetry()
        
        try:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(telemetry, f, indent=4)
            
            fan_state = telemetry["devices"]["fan"]["status"]
            light_state = telemetry["devices"]["light"]["status"]
            maint_state = telemetry["needs_maintenance"]
            
            print(f"[UPDATED] Fan: {fan_state} | Light: {light_state} | Maintenance Needed: {maint_state}")
        except Exception as e:
            print(f"[ERROR] Failed writing JSON: {e}")

        time.sleep(10)