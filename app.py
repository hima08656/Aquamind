
import json
import threading

import pandas as pd
import streamlit as st
import paho.mqtt.client as mqtt

st.set_page_config(
    page_title="AquaMind Live Dashboard",
    page_icon="🌱",
    layout="wide"
)

BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC = "aquamind/hima08656/sensors"


@st.cache_resource
def start_mqtt():
    state = {
        "latest": None,
        "connected": False,
        "error": None,
        "history": []
    }
    lock = threading.Lock()

    def on_connect(client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            with lock:
                state["connected"] = True
                state["error"] = None
            client.subscribe(TOPIC)
        else:
            with lock:
                state["connected"] = False
                state["error"] = str(reason_code)

    def on_disconnect(client, userdata, disconnect_flags, reason_code, properties):
        with lock:
            state["connected"] = False

    def on_message(client, userdata, message):
        try:
            reading = json.loads(message.payload.decode("utf-8"))
            reading["received_at"] = pd.Timestamp.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            with lock:
                state["latest"] = reading
                state["history"].append(reading)
                state["history"] = state["history"][-100:]
        except Exception as error:
            with lock:
                state["error"] = str(error)

    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id="AquaMindDashboard"
    )
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message

    try:
        client.connect(BROKER, PORT, keepalive=60)
        client.loop_start()
    except Exception as error:
        state["error"] = str(error)

    return state, lock


state, lock = start_mqtt()

st.title("🌱 AquaMind - Live Smart Irrigation")
st.caption(f"MQTT topic: {TOPIC}")

@st.fragment(run_every=3)
def live_dashboard():
    with lock:
        connected = state["connected"]
        error = state["error"]
        latest = (
            dict(state["latest"])
            if state["latest"] else None
        )
        history = [dict(row) for row in state["history"]]

    if connected:
        st.success("Connected to MQTT broker")
    else:
        st.warning("Connecting to MQTT broker...")
        if error:
            st.error(f"Connection/message error: {error}")

    if latest is None:
        st.info(
            "Waiting for sensor readings. Start your Wokwi simulation "
            "and wait for its next MQTT message."
        )
        return

    st.caption(
        f"Last received: {latest.get('received_at', 'Unknown')}"
    )

    a, b, c = st.columns(3)
    a.metric(
        "🌡️ Temperature",
        f"{latest.get('temperature_c', 'N/A')} °C"
    )
    b.metric(
        "💧 Humidity",
        f"{latest.get('humidity_pct', 'N/A')} %"
    )
    c.metric(
        "🌱 Soil Moisture",
        f"{latest.get('soil_moisture_pct', 'N/A')} %"
    )

    d, e, f = st.columns(3)
    d.metric(
        "🌧️ Rain Probability",
        f"{latest.get('rain_probability_pct', 'N/A')} %"
    )
    e.metric(
        "🧪 Simulated Soil EC",
        latest.get("soil_ec_simulated", "N/A")
    )
    f.metric(
        "🚿 Pump Status",
        latest.get("pump_status", "N/A")
    )

    st.subheader("💡 Irrigation Recommendation")
    moisture = latest.get("soil_moisture_pct")
    rain = latest.get("rain_probability_pct")

    if moisture is not None and rain is not None:
        if moisture < 30 and rain < 50:
            st.warning("Soil moisture is low. Irrigation may be needed.")
        elif rain >= 70:
            st.info("Rain probability is high. Consider delaying irrigation.")
        elif moisture >= 45:
            st.success("Soil moisture is sufficient.")
        else:
            st.info("Continue monitoring soil moisture.")

    st.subheader("📈 Live Sensor History")

    if history:
        chart_data = pd.DataFrame(history)
        chart_columns = [
            col for col in [
                "temperature_c",
                "humidity_pct",
                "soil_moisture_pct",
                "rain_probability_pct",
                "soil_ec_simulated"
            ]
            if col in chart_data.columns
        ]

        if chart_columns:
            st.line_chart(chart_data[chart_columns])

        st.subheader("Recent Readings")
        st.dataframe(
            chart_data.iloc[::-1],
            use_container_width=True,
            hide_index=True
        )

live_dashboard()
