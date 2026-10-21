
import streamlit as st
import pandas as pd
import json
from pathlib import Path
from datetime import datetime

# ---------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------

st.set_page_config(
    page_title="AquaMind Dashboard",
    page_icon="🌱",
    layout="wide"
)

# ---------------------------------------
# FILE PATH
# CSV is in the same folder as app.py
# ---------------------------------------

CSV_FILE = Path(__file__).parent / "aquamind_data.csv"

# ---------------------------------------
# DASHBOARD TITLE
# ---------------------------------------

st.title("🌱 AquaMind - Smart Irrigation Dashboard")

st.markdown(
    "Monitor virtual soil conditions and sensor readings "
    "from your Wokwi ESP32 prototype."
)

st.divider()

# ---------------------------------------
# LOAD CSV DATA
# ---------------------------------------

@st.cache_data(ttl=5)
def load_data(file_path, modified_time):
    return pd.read_csv(file_path)

if not CSV_FILE.exists():
    st.error("Sensor data file not found!")
    st.write("Expected file location:")
    st.code(str(CSV_FILE))
    st.info(
        "Upload aquamind_data.csv to the same GitHub "
        "folder as app.py."
    )
    st.stop()

try:
    data = load_data(
        str(CSV_FILE),
        CSV_FILE.stat().st_mtime
    )
except Exception as error:
    st.error(f"Could not read sensor data: {error}")
    st.stop()

if data.empty:
    st.warning("CSV file is empty. Waiting for sensor data.")
    st.stop()

# ---------------------------------------
# CLEAN COLUMN NAMES
# ---------------------------------------

data.columns = data.columns.str.strip()

# Support common column-name variations
data = data.rename(columns={
    "temperature": "temperature_c",
    "temperature_celsius": "temperature_c",
    "humidity": "humidity_pct",
    "soil_moisture": "soil_moisture_pct",
    "rain_probability": "rain_probability_pct",
    "soil_ec": "soil_ec_simulated",
    "light": "light_raw",
    "pump": "pump_status"
})

# Convert numeric sensor columns safely
numeric_columns = [
    "temperature_c",
    "humidity_pct",
    "soil_moisture_pct",
    "rain_probability_pct",
    "soil_ec_simulated",
    "light_raw"
]

for column in numeric_columns:
    if column in data.columns:
        data[column] = pd.to_numeric(
            data[column], errors="coerce"
        )

# ---------------------------------------
# CHECK REQUIRED COLUMNS
# ---------------------------------------

required_columns = [
    "temperature_c",
    "humidity_pct",
    "soil_moisture_pct",
    "rain_probability_pct",
    "soil_ec_simulated",
    "pump_status"
]

missing_columns = [
    column for column in required_columns
    if column not in data.columns
]

if missing_columns:
    st.error("Some required columns are missing:")
    st.write(missing_columns)
    st.write("Available CSV columns:")
    st.write(data.columns.tolist())
    st.stop()

# ---------------------------------------
# LATEST SENSOR READING
# ---------------------------------------

latest = data.iloc[-1]

temperature = latest["temperature_c"]
humidity = latest["humidity_pct"]
moisture = latest["soil_moisture_pct"]
rain = latest["rain_probability_pct"]
ec = latest["soil_ec_simulated"]
pump_status = str(latest["pump_status"]).upper()

# ---------------------------------------
# SENSOR METRICS
# ---------------------------------------

st.subheader("📊 Latest Sensor Readings")

c1, c2, c3 = st.columns(3)

c1.metric(
    "🌡️ Temperature",
    f"{temperature:.1f} °C"
    if pd.notna(temperature) else "N/A"
)

c2.metric(
    "💧 Humidity",
    f"{humidity:.1f} %"
    if pd.notna(humidity) else "N/A"
)

c3.metric(
    "🌱 Soil Moisture",
    f"{moisture:.1f} %"
    if pd.notna(moisture) else "N/A"
)

c4, c5, c6 = st.columns(3)

c4.metric(
    "🌧️ Rain Probability",
    f"{rain:.1f} %"
    if pd.notna(rain) else "N/A"
)

c5.metric(
    "🧪 Simulated Soil EC",
    f"{ec:.2f}"
    if pd.notna(ec) else "N/A"
)

c6.metric("🚿 Pump Status", pump_status)

# ---------------------------------------
# IRRIGATION RECOMMENDATION
# ---------------------------------------

st.divider()
st.subheader("💡 Irrigation Recommendation")

if pd.notna(moisture) and pd.notna(rain):
    if moisture < 30 and rain < 50:
        st.warning(
            "Soil moisture is low. Irrigation may be needed."
        )
    elif rain >= 70:
        st.info(
            "Rain probability is high. Consider delaying irrigation."
        )
    elif moisture >= 45:
        st.success(
            "Soil moisture is sufficient based on the demo threshold."
        )
    else:
        st.info(
            "Monitor soil moisture and rain probability."
        )
else:
    st.info("Not enough sensor data to make a recommendation.")

# ---------------------------------------
# SENSOR HISTORY CHARTS
# ---------------------------------------

st.divider()
st.subheader("📈 Sensor History")

chart_columns = [
    column for column in [
        "temperature_c",
        "humidity_pct",
        "soil_moisture_pct",
        "rain_probability_pct",
        "soil_ec_simulated"
    ]
    if column in data.columns
]

if chart_columns:
    st.line_chart(data[chart_columns].tail(100))
else:
    st.info("No numeric sensor columns are available for charts.")

# ---------------------------------------
# LIGHT SENSOR
# ---------------------------------------

if "light_raw" in data.columns:
    st.subheader("☀️ Light Sensor")
    st.line_chart(data[["light_raw"]].tail(100))

# ---------------------------------------
# RECENT SENSOR DATA
# ---------------------------------------

st.divider()
st.subheader("🗂️ Recent Sensor Records")

st.dataframe(
    data.tail(20).iloc[::-1],
    use_container_width=True,
    hide_index=True
)

# ---------------------------------------
# DOWNLOAD CSV
# ---------------------------------------

st.download_button(
    label="⬇️ Download Sensor Data CSV",
    data=data.to_csv(index=False).encode("utf-8"),
    file_name="aquamind_sensor_data.csv",
    mime="text/csv"
)

# ---------------------------------------
# DATA SOURCE INFORMATION
# ---------------------------------------

st.divider()

st.caption(
    f"Data source: {CSV_FILE.name} | "
    f"Total records: {len(data)}"
)

st.caption(
    "Note: This deployed dashboard reads the CSV file "
    "available in the repository. It does not directly "
    "receive live MQTT messages from your laptop."
)

if st.button("🔄 Refresh Dashboard"):
    st.cache_data.clear()
    st.rerun()
