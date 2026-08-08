import random, time

devices = {
    "fan":   {"status": False, "watts": 50},
    "light": {"status": True,  "watts": 10},
    "ac":    {"status": False, "watts": 1500},
}

def get_sensor_data():
    return {
        "temperature": round(random.uniform(24, 35), 1),
        "humidity":    round(random.uniform(40, 80), 1),
        "devices":     devices,
        "timestamp":   time.time()
    }

def toggle_device(name: str):
    if name in devices:
        devices[name]["status"] = not devices[name]["status"]
        return devices[name]
    return None

def calculate_bill(hours: float = 24):
    total_kwh = sum(
        d["watts"] * hours / 1000
        for d in devices.values() if d["status"]
    )
    return {
        "kwh":      round(total_kwh, 3),
        "bill_inr": round(total_kwh * 8, 2)
    }