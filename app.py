import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from streamlit_autorefresh import st_autorefresh
import plotly.graph_objects as go
import plotly.express as px
import io
from gtts import gTTS

# ---------------- AI VOICE ALERTS ----------------
VOICE_ALERTS = {
    "pump_on": {
        "en": "Warning. Soil is dry. Pump is now active.",
        "ml": "മണ്ണിൽ നനവില്ല. പമ്പ് ഓൺ ആയി.", # Malayalam
        "hi": "मिट्टी सूख गई है। पंप चालू हो गया है।", # Hindi
        "kn": "ಮಣ್ಣು ಒಣಗಿದೆ. ಪಂಪ್ ಆನ್ ಆಗಿದೆ." # Kannada
    },
    "pump_off": {
        "en": "Soil moisture is optimal. Pump disabled.",
        "ml": "മണ്ണിൽ നനവുണ്ട്. പമ്പ് ഓഫ് ആയി.",
        "hi": "मिट्टी में नमी है। पंप बंद है।",
        "kn": "ಮಣ್ಣಿನಲ್ಲಿ ತೇವಾಂಶವಿದೆ. ಪಂಪ್ ಆಫ್ ಆಗಿದೆ."
    },
    "rain": {
         "en": "Rain forecast detected. Irrigation paused.",
         "ml": "മഴ വരാൻ സാധ്യതയുണ്ട്. സിസ്റ്റം നിർത്തിവെച്ചു.", 
         "hi": "बारिश की संभावना है। पंप बंद है।",
         "kn": "ಮಳೆ ಬರುವ ಸಾಧ್ಯತೆ ಇದೆ. ಪಂಪ್ ಆಫ್ ಆಗಿದೆ."
    },
    "heat_warning": {
         "en": "Extreme heat detected. Monitoring soil closely.",
         "ml": "കടുത്ത ചൂട്. മണ്ണ് നിരീക്ഷിക്കുന്നു.", 
         "hi": "अत्यधिक गर्मी। मिट्टी की निगरानी कर रहे हैं।",
         "kn": "ವಿಪರೀತ ಶಾಖ. ಮಣ್ಣನ್ನು ಗಮನಿಸಲಾಗುತ್ತಿದೆ."
    }
}

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="AIoT Dashboard", page_icon="🌿", layout="wide")

# --- BROWSER AUDIO UNLOCK LOGIC ---
if "audio_unlocked" not in st.session_state:
    st.session_state.audio_unlocked = False

if not st.session_state.audio_unlocked:
    st.warning("🔇 Browser security requires authorization to enable the automatic AI Voice Assistant.")
    if st.button("🔊 AUTHORIZE & START DASHBOARD", use_container_width=True):
        st.session_state.audio_unlocked = True
        st.rerun()
    st.stop() # Halts the page from loading until they click

st_autorefresh(interval=30000, key="refresh")

# ---------------- CUSTOM CSS ----------------
st.markdown("""
<style>
    .stApp { background-color: #050b05; font-family: 'Inter', sans-serif; }
    .block-container { padding: 2rem 3rem !important; }
    .dash-title {
        font-size: 2rem;
        font-weight: 800;
        color: #4ade80;
        letter-spacing: 0.02em;
        margin-bottom: 0.5rem;
        text-shadow: 0 0 20px rgba(74, 222, 128, 0.2);
    }
    [data-testid="metric-container"] {
        background: linear-gradient(145deg, #0a150a 0%, #0d1a0d 100%);
        border: 1px solid #1a3a1a;
        border-radius: 12px;
        padding: 1rem 1.2rem !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.5);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    [data-testid="metric-container"]:hover {
        transform: translateY(-2px);
        border-color: #2e662e;
    }
    [data-testid="metric-container"] label {
        color: #8bba8b !important;
        font-size: 0.75rem !important;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        font-weight: 600;
    }
    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: #4ade80 !important;
        font-size: 1.6rem !important;
        font-weight: 700;
        margin-top: 0.3rem;
    }
    hr { border-color: #1a3a1a !important; margin: 1.5rem 0 !important; }
    .stMarkdown h3 {
        color: #4ade80 !important;
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        margin-bottom: 1rem !important;
        letter-spacing: 0.05em;
    }
    [data-testid="stSidebar"] { background-color: #030803 !important; border-right: 1px solid #1a3a1a; }
    [data-testid="stSidebar"] .stRadio label { color: #e2e8f0 !important; font-weight: 500; }
    .stSuccess, .stWarning, .stError, .stInfo {
        padding: 0.8rem 1rem !important;
        font-size: 0.9rem !important;
        border-radius: 8px !important;
        font-weight: 500;
    }
    .weather-banner-rain {
        background: linear-gradient(135deg, #1e3a5f, #0f2040);
        border: 1px solid #3b82f6;
        border-left: 4px solid #3b82f6;
        border-radius: 8px;
        padding: 0.6rem 1rem;
        color: #93c5fd;
        font-weight: 600;
        font-size: 0.9rem;
        margin-bottom: 0.5rem;
    }
    .weather-banner-clear {
        background: linear-gradient(135deg, #0a2a0a, #0f3a0f);
        border: 1px solid #4ade80;
        border-left: 4px solid #4ade80;
        border-radius: 8px;
        padding: 0.6rem 1rem;
        color: #4ade80;
        font-weight: 600;
        font-size: 0.9rem;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# ---------------- TITLE ----------------
st.markdown('<div class="dash-title">🌿 Edge AIoT Smart Irrigation Control Panel</div>', unsafe_allow_html=True)
st.caption("Real-Time Telemetry & Predictive Analytics Dashboard")
st.markdown("<br>", unsafe_allow_html=True)

# ---------------- GOOGLE SHEETS AUTH ----------------
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

@st.cache_resource
def get_client():
    import json
    creds_dict = json.loads(st.secrets["gcp_service_account"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        creds_dict, scope
    )
    return gspread.authorize(creds)

client = get_client()

@st.cache_resource(ttl=300)
def get_sheet():
    return client.open("SmartIrrigationData").sheet1

sheet = get_sheet()

# ---------------- LOAD DATA ----------------
@st.cache_data(ttl=30)
def load_data():
    try:
        data = pd.DataFrame(sheet.get_all_records())
        if not data.empty:
            st.session_state["last_df"] = data
        return data
    except:
        return pd.DataFrame()

df = load_data()

if df.empty:
    if "last_df" in st.session_state:
        df = st.session_state["last_df"]
    else:
        st.info("⏳ Connecting to ESP32 / Waiting for telemetry...")
        st.stop()

for col in ["soil", "rain", "decision", "pump_time", "pump_count", "temp", "humidity", "soil_pct", "adaptive_threshold", "rain_forecast"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

latest = df.iloc[-1]

# ---------------- SESSION STATE ----------------
if "override" not in st.session_state:
    st.session_state.override = -1

# ---------------- WRITE FUNCTION ----------------
def update_override(value):
    try:
        sheet.update_cell(2, 6, value)
    except:
        st.warning("Sheet update failed")

# ---------------- CONTROL PANEL ----------------
st.sidebar.header("⚙️ Control Mode")

mode = st.sidebar.radio("Select System Mode", ["AUTO (AI Edge)", "MANUAL OVERRIDE"])

if mode == "MANUAL OVERRIDE":
    st.sidebar.markdown("---")
    st.sidebar.write("Pump Control")

    if st.sidebar.button("🔴 TURN ON PUMP", use_container_width=True):
        st.session_state.override = 1
        update_override(1)

    if st.sidebar.button("🟢 TURN OFF PUMP", use_container_width=True):
        st.session_state.override = 0
        update_override(0)
else:
    st.session_state.override = -1
    update_override(-1)

st.sidebar.markdown("---")
st.sidebar.info("💡 **AI Adaptive Threshold** dynamically adjusts the soil dryness limit based on ambient temperature to prevent water stress.")

# ---------------- AI VOICE ASSISTANT SETTINGS ----------------
st.sidebar.markdown("---")
st.sidebar.header("🗣️ AI Voice Assistant")
lang_map = {"English": "en", "Malayalam": "ml", "Hindi": "hi", "Kannada": "kn"}
selected_lang = st.sidebar.selectbox("Broadcast Language", list(lang_map.keys()))
ai_lang = lang_map[selected_lang]

# Saves the language to Google Sheets for the Backend script to read
try:
    sheet.update_cell(2, 8, ai_lang)
except:
    pass

# ---------------- WEATHER FORECAST BANNER ----------------
rain_forecast_val = int(latest.get("rain_forecast", 0)) if "rain_forecast" in latest else 0

if rain_forecast_val == 1:
    st.markdown(
        '<div class="weather-banner-rain">🌧 WEATHER AI ACTIVE — Rain forecast detected! Irrigation automatically suppressed to conserve water.</div>',
        unsafe_allow_html=True
    )
else:
    st.markdown(
        '<div class="weather-banner-clear">☀ WEATHER AI — Sky clear. No rain forecast. System operating in normal AUTO mode.</div>',
        unsafe_allow_html=True
    )

# ---------------- TRIGGER VISIBLE AI VOICE ----------------
def generate_audio_bytes(alert_type):
    text = VOICE_ALERTS[alert_type][ai_lang]
    tts = gTTS(text=text, lang=ai_lang)
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    fp.seek(0)
    
    st.session_state.latest_audio_bytes = fp.read()
    st.session_state.latest_audio_text = text
    st.toast(f"🗣️ AI Assistant: {text}")

# State tracking to remember the previous refresh cycle
if "last_pump" not in st.session_state:
    st.session_state.last_pump = latest.get("decision", 0)
if "last_rain" not in st.session_state:
    st.session_state.last_rain = rain_forecast_val
if "last_temp" not in st.session_state:
    st.session_state.last_temp = latest.get("temp", 0)

current_pump = latest.get("decision", 0)
current_temp = latest.get("temp", 0)

# Check for state changes and trigger voice generation
if current_pump == 1 and st.session_state.last_pump == 0:
    generate_audio_bytes("pump_on")
elif current_pump == 0 and st.session_state.last_pump == 1:
    generate_audio_bytes("pump_off")
elif rain_forecast_val == 1 and st.session_state.last_rain == 0:
    generate_audio_bytes("rain")
elif current_temp >= 35 and st.session_state.last_temp < 35:
    generate_audio_bytes("heat_warning")

# Update memory for the next refresh
st.session_state.last_pump = current_pump
st.session_state.last_rain = rain_forecast_val
st.session_state.last_temp = current_temp

# --- VISIBLE AUDIO PLAYER ---
if "latest_audio_bytes" in st.session_state:
    st.info(f"🗣️ **Latest AI Broadcast:** {st.session_state.latest_audio_text}")
    st.audio(st.session_state.latest_audio_bytes, format="audio/mp3", autoplay=True)
else:
    st.info("🗣️ **AI Voice Assistant:** Standing by. No active voice broadcasts.")


# =========================================================
# METRICS ROW 1 — PRIMARY
# =========================================================
m1, m2, m3, m4, m5, m6 = st.columns(6)

m1.metric("Moisture", f"{round(latest.get('soil_pct', 0), 1)}%" if "soil_pct" in latest else "N/A")
m2.metric("Temp (°C)", round(latest.get("temp", 0), 1) if "temp" in latest else "N/A")
m3.metric("Humidity", f"{round(latest.get('humidity', 0), 1)}%" if "humidity" in latest else "N/A")
m4.metric("Rain Sensor", "☔ YES" if latest.get("rain", 0) == 1 else "☀ NO")
m5.metric("Rain Forecast", "🌧 YES" if rain_forecast_val == 1 else "☀ NO")
m6.metric("Pump Status", "🔴 ACTIVE" if latest.get("decision", 0) == 1 else "🟢 STANDBY")

st.markdown("<br>", unsafe_allow_html=True)

# =========================================================
# METRICS ROW 2 — SECONDARY & AI
# =========================================================
s1, s2, s3, s4, s5 = st.columns(5)

s1.metric("Soil Raw Value", int(latest.get("soil", 0)))
s2.metric("AI Threshold", int(latest.get("adaptive_threshold", 2500)) if "adaptive_threshold" in latest else "N/A")
s3.metric("Pump Activations", int(df["pump_count"].max()) if "pump_count" in df else 0)
s4.metric("Total Pump Time(ms)", f"{int(latest.get('pump_time', 0)):,}")
s5.metric("Telemetry Records", len(df))

st.divider()

# =========================================================
# GAUGE + STATUS + AI CHART
# =========================================================
col_gauge, col_status, col_ai_chart = st.columns([1, 1, 2])

with col_gauge:
    st.markdown("### 🌱 Real-time Moisture")

    soil_pct_val = float(latest.get("soil_pct", 0)) if "soil_pct" in latest else 0.0

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=soil_pct_val,
        number={"suffix": "%", "font": {"color": "#4ade80", "size": 36, "family": "Inter"}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#4ade80"},
            "bar": {"color": "#4ade80"},
            "bgcolor": "#0d1a0d",
            "bordercolor": "#1a3a1a",
            "steps": [
                {"range": [0, 30],  "color": "#ef4444"},
                {"range": [30, 60], "color": "#eab308"},
                {"range": [60, 100],"color": "#22c55e"}
            ],
            "threshold": {
                "line": {"color": "white", "width": 3},
                "thickness": 0.75,
                "value": 35
            }
        }
    ))

    fig.update_layout(
        height=250,
        margin=dict(t=20, b=10, l=10, r=10),
        paper_bgcolor="rgba(0,0,0,0)",
        font={"color": "#4ade80", "family": "Inter"}
    )
    st.plotly_chart(fig, use_container_width=True)

with col_status:
    st.markdown("### ⚡ System Diagnostics")

    if st.session_state.override == -1:
        st.success("🧠 Edge AI Control: ACTIVE")
    else:
        st.warning("⚠️ Manual Override: ENGAGED")

    if latest.get("decision", 0) == 1:
        st.error("💧 Irrigation: DISPENSING WATER")
    else:
        st.info("✅ Irrigation: IDLE")

    if latest.get("rain", 0) == 1:
        st.info("☔ Rain Sensor: DETECTED")
    else:
        st.success("☀ Rain Sensor: CLEAR")

    # Weather forecast status
    if rain_forecast_val == 1:
        st.warning("🌧 Weather AI: RAIN FORECAST")
    else:
        st.success("☀ Weather AI: CLEAR SKY")

    if len(df) > 0 and "decision" in df.columns:
        pump_on = df["decision"].sum()
        efficiency = round(((len(df) - pump_on) / len(df)) * 100, 1)
        st.markdown(f"**Resource Efficiency:** `{efficiency}%`")

with col_ai_chart:
    st.markdown("### 🧠 AI Adaptive Threshold vs Soil Dynamics")

    if "time" in df.columns and "soil" in df.columns and "adaptive_threshold" in df.columns:
        df_ai = df.set_index("time").tail(50)

        fig_ai = go.Figure()

        fig_ai.add_trace(go.Scatter(
            x=df_ai.index, y=df_ai["soil"],
            mode='lines', name='Raw Soil Moisture',
            line=dict(color='#3b82f6', width=2)
        ))

        fig_ai.add_trace(go.Scatter(
            x=df_ai.index, y=df_ai["adaptive_threshold"],
            mode='lines', name='AI Threshold Limit',
            line=dict(color='#ef4444', width=2, dash='dash')
        ))

        # Add rain forecast shading if available
        if "rain_forecast" in df_ai.columns:
            rain_periods = df_ai[df_ai["rain_forecast"] == 1]
            if not rain_periods.empty:
                fig_ai.add_trace(go.Scatter(
                    x=df_ai.index, y=[3200] * len(df_ai),
                    fill=None, mode='lines',
                    line=dict(color='rgba(0,0,0,0)'),
                    showlegend=False
                ))
                fig_ai.add_trace(go.Scatter(
                    x=df_ai.index,
                    y=[3200 if v == 1 else None for v in df_ai["rain_forecast"]],
                    fill='tozeroy',
                    fillcolor='rgba(59,130,246,0.1)',
                    mode='none',
                    name='Rain Forecast Period'
                ))

        fig_ai.update_layout(
            height=250,
            margin=dict(t=10, b=10, l=0, r=0),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis=dict(showgrid=False, showticklabels=False),
            yaxis=dict(gridcolor="#1a3a1a", zeroline=False),
            font=dict(color="#8bba8b")
        )
        st.plotly_chart(fig_ai, use_container_width=True)
    else:
        st.warning("Waiting for sufficient telemetry data...")

st.divider()

# =========================================================
# HISTORICAL TRENDS ROW
# =========================================================
st.markdown("### 📊 Environmental & Mechanical Telemetry")
t1, t2, t3, t4, t5 = st.columns(5)

with t1:
    st.caption("Temperature (°C)")
    if "temp" in df.columns and "time" in df.columns:
        st.line_chart(df.set_index("time")["temp"], height=150, color="#f97316")

with t2:
    st.caption("Humidity (%)")
    if "humidity" in df.columns and "time" in df.columns:
        st.line_chart(df.set_index("time")["humidity"], height=150, color="#06b6d4")

with t3:
    st.caption("Cumulative Pump Operation (ms)")
    if "pump_time" in df.columns and "time" in df.columns:
        st.area_chart(df.set_index("time")["pump_time"], height=150, color="#8b5cf6")

with t4:
    st.caption("Pump Activation Cycles")
    if "pump_count" in df.columns and "time" in df.columns:
        st.line_chart(df.set_index("time")["pump_count"], height=150, color="#10b981")

with t5:
    st.caption("Rain Forecast Status")
    if "rain_forecast" in df.columns and "time" in df.columns:
        st.area_chart(df.set_index("time")["rain_forecast"], height=150, color="#3b82f6")

# ---------------- FOOTER ----------------
st.markdown("---")
st.markdown(
    '<p style="text-align:center; color:#2d5a2d; font-size:0.7rem; letter-spacing:0.1em;">⚡ EDGE AIoT SMART IRRIGATION &nbsp;|&nbsp; REAL-TIME MONITORING &nbsp;|&nbsp; IEEE RESEARCH PROJECT &nbsp;|&nbsp; Bengaluru, India</p>',
    unsafe_allow_html=True
)
