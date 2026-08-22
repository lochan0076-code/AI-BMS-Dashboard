import os
import json
import random
import time
from datetime import datetime

# Fallback structure if bms_data.json is missing or unreadable
FALLBACK_BMS_DATA = {
    "device_id": "AI-BMS-PI3B",
    "timestamp": datetime.now().astimezone().isoformat(),
    "online": True,
    "temperature": 28.6,
    "humidity": 61.4,
    "voltage": 51.8,
    "current": 2.35,
    "power": 121.73,
    "battery_soc": 78.5,
    "battery_status": "NORMAL",
    "safety": {
        "smoke": False,
        "spark": False,
        "flame": False,
        "fire": False
    },
    "devices": {
        "fan": {"status": False, "watts": 50},
        "light": {"status": True, "watts": 10},
        "bms": {"status": True, "watts": 5}
    },
    "alerts": [],
    "test_mode": False
}

def _find_bms_data_path():
    """Find bms_data.json relative to backend file or current working directory."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(base_dir, "..", "bms_data.json"),
        os.path.join(base_dir, "..", "..", "bms_data.json"),
        os.path.join(base_dir, "..", "AI-BMS-Dashboard", "bms_data.json"),
        os.path.join(os.getcwd(), "bms_data.json"),
        os.path.join(os.getcwd(), "AI-BMS-Dashboard", "bms_data.json"),
    ]
    for candidate in candidates:
        if os.path.isfile(candidate):
            return candidate
    return None

def load_bms_data():
    """Load JSON template with safe fallback."""
    json_path = _find_bms_data_path()
    if json_path:
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {json_path}: {e}. Using fallback data.")
    return json.loads(json.dumps(FALLBACK_BMS_DATA))

# Initialize mutable state from JSON template or fallback
_base_data = load_bms_data()
devices = _base_data.get("devices", {
    "fan": {"status": True, "watts": 50},
    "light": {"status": True, "watts": 10},
    "bms": {"status": True, "watts": 5}
})

# Ensure "bms" is present and "ac" is removed if legacy structure was loaded
if "ac" in devices:
    devices["bms"] = devices.pop("ac")
    devices["bms"]["watts"] = 5
if "bms" not in devices:
    devices["bms"] = {"status": True, "watts": 5}

def get_sensor_data():
    """
    Returns updated sensor data structure adhering to bms_data.json.
    Modular design ready for real Raspberry Pi sensor readings (e.g. DHT22, INA219, MQ-2).
    """
    # Load base template structure
    data = load_bms_data()
    
    # Update live timestamp
    data["timestamp"] = datetime.now().astimezone().isoformat()
    
    # Simulate slight live sensor fluctuations (Replace these with real RPi GPIO readings later)
    data["temperature"] = round(data.get("temperature", 28.6) + random.uniform(-0.5, 0.5), 1)
    data["humidity"] = round(data.get("humidity", 61.4) + random.uniform(-1.0, 1.0), 1)
    
    # Maintain live mutable device status
    data["devices"] = devices
    
    # Calculate live power consumption based on active devices
    active_device_watts = sum(d["watts"] for d in devices.values() if d.get("status", False))
    data["power"] = round(100.0 + active_device_watts + random.uniform(-2.0, 2.0), 2)
    
    # Derive current (P = V * I -> I = P / V)
    voltage = data.get("voltage", 51.8)
    data["current"] = round(data["power"] / voltage, 2)
    
    # Dynamic safety alerts check (mocked / scalable for real hardware sensors)
    temp = data["temperature"]
    smoke = temp > 50.0 or data.get("safety", {}).get("smoke", False)
    spark = temp > 60.0 or data.get("safety", {}).get("spark", False)
    flame = spark or data.get("safety", {}).get("flame", False)
    fire = smoke and spark
    
  

    data["safety"] = {
        "smoke": smoke,
        "spark": spark,
        "flame": flame,
        "fire": fire
    }
    
    # Dynamic alerts array
    # Dynamic alerts array
    alerts = []
    if smoke: alerts.append("Smoke detected")
    if spark or flame: alerts.append("Spark/Flame detected")
    if fire: alerts.append("CRITICAL: Fire Hazard Detected")
    
    data["alerts"] = alerts
    
    return data

def toggle_device(name: str):
    """Toggle device status in mutable device state."""
    if name in devices:
        devices[name]["status"] = not devices[name]["status"]
        return devices[name]
    return None


