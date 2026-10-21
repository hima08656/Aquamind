from pathlib import Path

import pandas as pd
import streamlit as st

# File location
DATA_FILE = Path(__file__).parent / "data" / "aquamind_data.csv"

# Dashboard configuration
st.set_page_config(
    page_title="AquaMind Dashboard",
    page_icon="🌱",
    layout="wide",
)

st.title("🌱 AquaMind")
st.subheader("Smart Irrigation Monitoring Dashboard")
st.caption("Wokwi ESP32 • MQTT • Python • CSV Data Logging")

# Refresh button
if st.button("🔄 Refresh Sensor Data"):
    st.rerun()

# Load sensor data
if not DATA_FILE.exists():
    st.warning("Sensor data file not found. Start mqtt_subscriber.py first.")
    st.stop()

try:
    df = pd.read_csv(DATA_FILE)
except (OSError, pd.errors.EmptyDataError):
    st.warning("No sensor data available yet.")
    st.stop()

if df.empty:
    st.info("Waiting for sensor readings...")
    st.stop()

# Convert columns to numeric values
numeric_columns = [
    "temperature_c",
    "humidity_pct",
    "soil_moisture_pct",
    "rain_probability_pct",
    "soil_ec_simulated",
    "light_raw",
]

for column in numeric_columns:
    df[column] = pd.to_numeric(df[column], errors="coerce")

latest = df.iloc[-1]

# Latest readings
st.header("📊 Latest Sensor Readings")

c1, c2, c3 = st.columns(3)

c1.metric(
    "Temperature",
    f"{latest['temperature_c']:.1f} °C"
)

c2.metric(
    "Humidity",
    f"{latest['humidity_pct']:.1f} %"
)

c3.metric(
    "Soil Moisture",
    f"{latest['soil_moisture_pct']:.0f} %"
)

c4, c5, c6 = st.columns(3)

c4.metric(
    "Rain Probability",
    f"{latest['rain_probability_pct']:.0f} %"
)

c5.metric(
    "Simulated Soil EC",
    f"{latest['soil_ec_simulated']:.2f}"
)

c6.metric(
    "Light Sensor",
    f"{latest['light_raw']:.0f}"
)

# Irrigation status
st.header("💧 Irrigation Status")

pump_status = str(latest.get("pump_status", "UNKNOWN")).upper()

if pump_status == "ON":
    st.success("Pump Indicator: ON")
elif pump_status == "OFF":
    st.info("Pump Indicator: OFF")
else:
    st.warning(f"Pump Status: {pump_status}")

st.write(
    "**Irrigation reason:**",
    latest.get("irrigation_reason", "Not available"),
)

# Sensor history chart
st.header("📈 Sensor History")

chart_options = {
    "Temperature (°C)": "temperature_c",
    "Humidity (%)": "humidity_pct",
    "Soil Moisture (%)": "soil_moisture_pct",
    "Rain Probability (%)": "rain_probability_pct",
    "Simulated Soil EC": "soil_ec_simulated",
    "Light Sensor": "light_raw",
}

selected_sensor = st.selectbox(
    "Select a sensor to view its history",
    list(chart_options.keys()),
)

column = chart_options[selected_sensor]

chart_data = df.tail(100)[["timestamp", column]].copy()
chart_data[column] = pd.to_numeric(
    chart_data[column], errors="coerce"
)

if not chart_data.empty:
    st.line_chart(
        chart_data.set_index("timestamp")[[column]]
    )

# Recent readings table
st.header("📋 Recent Sensor Readings")

st.dataframe(
    df.tail(20).iloc[::-1],
    use_container_width=True,
)

# Download data
st.download_button(
    label="⬇️ Download Sensor Data CSV",
    data=DATA_FILE.read_bytes(),
    file_name="aquamind_sensor_data.csv",
    mime="text/csv",
)

st.caption(f"Total recorded readings: {len(df)}")
st.caption("Click Refresh Sensor Data to load new readings.")
