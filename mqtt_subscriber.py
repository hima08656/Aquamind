
import json
import csv
import time
from pathlib import Path
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

# MQTT configuration
BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC = "aquamind/hima08656/sensors"

# Data storage
DATA_DIR = Path(__file__).parent / "data"
CSV_FILE = DATA_DIR / "aquamind_data.csv"

HEADERS = [
    "timestamp",
    "device_id",
    "uptime_ms",
    "temperature_c",
    "humidity_pct",
    "soil_moisture_pct",
    "rain_probability_pct",
    "soil_ec_simulated",
    "light_raw",
    "pump_status",
    "irrigation_reason",
]

DATA_DIR.mkdir(exist_ok=True)

def save_data(data):
    file_exists = CSV_FILE.exists()

    with CSV_FILE.open("a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=HEADERS)

        if not file_exists or CSV_FILE.stat().st_size == 0:
            writer.writeheader()

        row = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **data,
        }

        writer.writerow({key: row.get(key, "") for key in HEADERS})

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print("MQTT connected successfully!")
        client.subscribe(TOPIC)
        print("Subscribed to:", TOPIC)
        print("Waiting for AquaMind sensor data...\n")
    else:
        print("MQTT connection failed:", reason_code)

def on_message(client, userdata, message):
    try:
        data = json.loads(message.payload.decode("utf-8"))

        required_fields = [
            "temperature_c",
            "humidity_pct",
            "soil_moisture_pct",
            "rain_probability_pct",
            "soil_ec_simulated",
            "light_raw",
            "pump_status",
        ]

        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing field: {field}")

        save_data(data)

        print("-" * 45)
        print("New AquaMind reading received!")
        print("Temperature:", data["temperature_c"], "C")
        print("Humidity:", data["humidity_pct"], "%")
        print("Soil moisture:", data["soil_moisture_pct"], "%")
        print("Rain probability:", data["rain_probability_pct"], "%")
        print("Simulated soil EC:", data["soil_ec_simulated"])
        print("Pump status:", data["pump_status"])
        print("Saved to:", CSV_FILE)

    except (json.JSONDecodeError, ValueError, OSError) as error:
        print("Could not process message:", error)

client = mqtt.Client(
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
    client_id=f"AquaMindPython-{int(time.time())}",
    protocol=mqtt.MQTTv311,
)

client.on_connect = on_connect
client.on_message = on_message
client.reconnect_delay_set(min_delay=1, max_delay=30)

print("Connecting to MQTT broker:", BROKER)

try:
    client.connect(BROKER, PORT, keepalive=60)
    client.loop_forever()
except KeyboardInterrupt:
    print("\nSubscriber stopped.")
    client.disconnect()
except OSError as error:
    print("Network/MQTT error:", error)
