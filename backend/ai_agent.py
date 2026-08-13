from groq import Groq
import json
import os
from pathlib import Path
from dotenv import load_dotenv

from backend.pi_mock import (
    get_sensor_data,
    toggle_device,
    calculate_bill,
)

# ---------------------------------------------------------
# LOAD ENVIRONMENT VARIABLES
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(dotenv_path=ENV_FILE)

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise RuntimeError(
        "GROQ_API_KEY is not set. Please add it to the .env file."
    )

client = Groq(api_key=api_key)

# ---------------------------------------------------------
# AI SYSTEM PROMPT
# ---------------------------------------------------------

SYSTEM = """You are the AI assistant for an AI-based Battery Management System (AI-BMS) dashboard.

You monitor a Raspberry Pi-based battery management system.

You can:
- Read battery temperature
- Read humidity
- Read voltage
- Read current
- Read power
- Read battery state of charge (SOC)
- Read battery status
- Read safety conditions
- Read the ON/OFF status of the BMS, fan, and light
- Calculate electricity usage and bill
- Control the BMS ON/OFF state

IMPORTANT DEVICE CONTROL RULES:

- The BMS is the ONLY device that can be controlled.
- The fan is MONITORING ONLY.
- The light is MONITORING ONLY.
- Never attempt to turn the fan ON or OFF.
- Never attempt to turn the light ON or OFF.
- If the user asks to control the fan or light, explain that these devices are monitoring-only and cannot be controlled from the dashboard.
- Never claim that a device was changed unless the backend actually changed it.

Reply concisely and clearly.
"""

# ---------------------------------------------------------
# AI AGENT
# ---------------------------------------------------------

def ask_agent(user_msg: str) -> str:

    state = json.dumps(
        get_sensor_data(),
        indent=2
    )

    bill = json.dumps(
        calculate_bill(),
        indent=2
    )

    context = (
        f"Current sensor state:\n{state}\n\n"
        f"Current bill (24h):\n{bill}"
    )

    user_lower = user_msg.lower()

    # -----------------------------------------------------
    # BMS CONTROL ONLY
    # -----------------------------------------------------

    if "bms" in user_lower:

        control_words = [
            "on",
            "off",
            "toggle",
            "turn",
            "switch",
        ]

        if any(
            word in user_lower
            for word in control_words
        ):

            result = toggle_device("bms")

            if result is not None:

                status = (
                    "ON"
                    if result.get("status")
                    else "OFF"
                )

                return f"BMS is now {status}."

    # -----------------------------------------------------
    # FAN / LIGHT ARE MONITORING ONLY
    # -----------------------------------------------------

    if "fan" in user_lower or "light" in user_lower:

        requested_device = (
            "fan"
            if "fan" in user_lower
            else "light"
        )

        control_words = [
            "on",
            "off",
            "toggle",
            "turn",
            "switch",
        ]

        if any(
            word in user_lower
            for word in control_words
        ):

            return (
                f"The {requested_device} is "
                "monitoring-only and cannot be "
                "controlled from the dashboard."
            )

    # -----------------------------------------------------
    # GROQ AI RESPONSE
    # -----------------------------------------------------

    try:

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM + "\n\n" + context,
                },
                {
                    "role": "user",
                    "content": user_msg,
                },
            ],
        )

        return response.choices[0].message.content

    except Exception as e:

        return f"AI Agent response unavailable: {e}"