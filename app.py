import streamlit as st
import pandas as pd
import gspread
from streamlit_autorefresh import st_autorefresh
import plotly.graph_objects as go
import io
from gtts import gTTS
from google.oauth2.service_account import Credentials
import json

# ---------------- AI VOICE ALERTS ----------------
VOICE_ALERTS = {
    "pump_on": {
        "en": "Warning. Soil is dry. Pump is now active.",
        "ml": "മണ്ണിൽ നനവില്ല. പമ്പ് ഓൺ ആയി.",
        "hi": "मिट्टी सूख गई है। पंप चालू हो गया है।",
        "kn": "ಮಣ್ಣು ಒಣಗಿದೆ. ಪಂಪ್ ಆನ್ ಆಗಿದೆ."
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

# ---------------- ADDITION 3: CROP PROFILES ----------------
CROP_PROFILES = {
    "Rice 🌾":        {"threshold": 2200, "description": "High water demand. Irrigates frequently."},
    "Wheat 🌿":       {"threshold": 2500, "description": "Moderate water demand. Standard irrigation."},
    "Vegetables 🥦":  {"threshold": 2700, "description": "Consistent moisture needed. Irrigates carefully."},
    "Flowers 🌸":     {"threshold": 2800, "description": "Sensitive to overwatering. Conservative irrigation."},
    "Custom ⚙️":      {"threshold": None, "description": "Set your own threshold manually."}
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
    st.stop()

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
    .dose-banner {
        background: linear-gradient(135deg, #2a1a3a, #1a0f2a);
        border: 1px solid #a78bfa;
        border-left: 4px solid #a78bfa;
        border-radius: 8px;
        padding: 0.6rem 1rem;
        color: #c4b5fd;
        font-weight: 600;
        font-size: 0.9rem;
        margin-bottom: 0.5rem;
    }
    .crop-banner {
        background: linear-gradient(135deg, #0a2a1a, #0f3a1f);
        border: 1px solid #4ade80;
        border-left: 4px solid #4ade80;
        border-radius: 8px;
        padding: 0.6rem 1rem;
        color: #86efac;
        font-weight: 600;
        font-size: 0.9rem;
        margin-bottom: 0.5rem;
    }
    .savings-banner {
        background: linear-gradient(135deg, #1a2a0a, #1f3a0f);
        border: 1px solid #84cc16;
        border-left: 4px solid #84cc16;
        border-radius: 8px;
        padding: 0.6rem 1rem;
        color: #bef264;
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
def get_sheet():
    creds_dict = json.loads(st.secrets["GOOGLE_CREDS"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(creds)
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
required_cols = [
    "soil", "rain", "decision", "pump_time", "pump_count",
    "temp", "humidity", "soil_pct", "adaptive_threshold", "rain_forecast",
    "rain_probability", "dose_factor", "water_ml"
]

for col in required_cols:
    if col not in df.columns:
        df[col] = 0 if col != "dose_factor" else 1.0

df = df.fillna(0)
for col in df.columns:
    if col != "time":
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

if df.empty:
    if "last_df" in st.session_state:
        df = st.session_state["last_df"]
    else:
        st.info("⏳ Waiting for ESP32 telemetry...")
        st.stop()

latest = df.iloc[-1]

# ---------------- SESSION STATE ----------------
if "override" not in st.session_state:
    st.session_state.override = -1

# ============================================================
# OVERRIDE WRITE FUNCTION
# ============================================================
def update_override(value):
    try:
        sheet.update_cell(1, 16, str(value))  # Row 1, Col P (16) = override command
        check = sheet.cell(1, 16).value
        if str(check) == str(value):
            if value == 1:
                st.success("✅ Command confirmed: PUMP ON")
            elif value == 0:
                st.success("✅ Command confirmed: PUMP OFF")
            else:
                st.success("✅ Command confirmed: AUTO MODE")
        else:
            st.error(f"❌ Write failed! Sheet shows: {check}")
    except Exception as e:
        st.error(f"Command error: {e}")

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
    if st.session_state.override != -1:
        st.session_state.override = -1
        update_override(-1)

st.sidebar.markdown("---")
st.sidebar.info("💡 **AI Adaptive Threshold** dynamically adjusts based on temperature.")
st.sidebar.info("💧 **Confidence-Weighted Dosing** scales pump duration by rain-forecast confidence.")

# ---------------- AI VOICE ASSISTANT SETTINGS ----------------
st.sidebar.markdown("---")
st.sidebar.header("🗣️ AI Voice Assistant")
lang_map = {"English": "en", "Malayalam": "ml", "Hindi": "hi", "Kannada": "kn"}
selected_lang = st.sidebar.selectbox("Broadcast Language", list(lang_map.keys()))
ai_lang = lang_map[selected_lang]

if "last_written_lang" not in st.session_state:
    st.session_state.last_written_lang = None

if st.session_state.last_written_lang != ai_lang:
    try:
        sheet.update_cell(1, 17, ai_lang)  # Row 1, Col Q (17) = language code
        st.session_state.last_written_lang = ai_lang
    except Exception:
        pass

# ---------------- ADDITION 3: CROP PROFILE SELECTOR ----------------
st.sidebar.markdown("---")
st.sidebar.header("🌾 Crop Profile")

selected_crop = st.sidebar.selectbox(
    "Select Your Crop",
    list(CROP_PROFILES.keys()),
    index=1  # default = Wheat
)

crop_info = CROP_PROFILES[selected_crop]

if selected_crop == "Custom ⚙️":
    custom_threshold = st.sidebar.number_input(
        "Set Soil Threshold (1800–3000)",
        min_value=1800, max_value=3000, value=2500, step=50
    )
    crop_threshold = custom_threshold
else:
    crop_threshold = crop_info["threshold"]

st.sidebar.caption(f"ℹ️ {crop_info['description']}")
st.sidebar.caption(f"Soil trigger threshold: **{crop_threshold}**")

if "last_written_crop" not in st.session_state:
    st.session_state.last_written_crop = None

if st.session_state.last_written_crop != crop_threshold:
    try:
        sheet.update_cell(1, 18, str(crop_threshold))  # Row 1, Col R (18) = crop threshold
        st.session_state.last_written_crop = crop_threshold
    except Exception:
        pass

# ---------------- WEATHER FORECAST BANNER ----------------
rain_forecast_val = latest.get("rain_forecast", 0)
rain_forecast_val = 0 if pd.isna(rain_forecast_val) else int(rain_forecast_val)

if rain_forecast_val == 1:
    st.markdown(
        '<div class="weather-banner-rain">🌧 WEATHER AI ACTIVE — Rain forecast detected! Irrigation dose is being scaled down to conserve water.</div>',
        unsafe_allow_html=True
    )
else:
    st.markdown(
        '<div class="weather-banner-clear">☀ WEATHER AI — Sky clear. No rain forecast. System operating with full-dose AUTO mode.</div>',
        unsafe_allow_html=True
    )

# ---------------- DOSE FACTOR BANNER ----------------
dose_val = float(latest.get("dose_factor", 1.0))
st.markdown(
    f'<div class="dose-banner">💧 CONFIDENCE-WEIGHTED DOSING — Last pump pulse ran at <b>{dose_val*100:.0f}%</b> of full duration based on rain-forecast confidence.</div>',
    unsafe_allow_html=True
)

# ---------------- ADDITION 3: CROP PROFILE BANNER ----------------
st.markdown(
    f'<div class="crop-banner">🌾 CROP PROFILE: <b>{selected_crop}</b> — Soil threshold set to <b>{crop_threshold}</b>. {crop_info["description"]}</div>',
    unsafe_allow_html=True
)

# ---------------- AI VOICE ALERTS ----------------
def generate_audio_bytes(alert_type):
    text = VOICE_ALERTS[alert_type][ai_lang]
    tts  = gTTS(text=text, lang=ai_lang)
    fp   = io.BytesIO()
    tts.write_to_fp(fp)
    fp.seek(0)
    st.session_state.latest_audio_bytes = fp.read()
    st.session_state.latest_audio_text  = text
    st.toast(f"🗣️ AI Assistant: {text}")

if "last_pump" not in st.session_state:
    st.session_state.last_pump = latest.get("decision", 0)
if "last_rain" not in st.session_state:
    st.session_state.last_rain = rain_forecast_val
if "last_temp" not in st.session_state:
    st.session_state.last_temp = latest.get("temp", 0)

current_pump = latest.get("decision", 0)
current_temp = latest.get("temp", 0)

if current_pump == 1 and st.session_state.last_pump == 0:
    generate_audio_bytes("pump_on")
elif current_pump == 0 and st.session_state.last_pump == 1:
    generate_audio_bytes("pump_off")
elif rain_forecast_val == 1 and st.session_state.last_rain == 0:
    generate_audio_bytes("rain")
elif current_temp >= 35 and st.session_state.last_temp < 35:
    generate_audio_bytes("heat_warning")

st.session_state.last_pump = current_pump
st.session_state.last_rain = rain_forecast_val
st.session_state.last_temp = current_temp

if "latest_audio_bytes" in st.session_state:
    st.info(f"🗣️ **Latest AI Broadcast:** {st.session_state.latest_audio_text}")
    st.audio(st.session_state.latest_audio_bytes, format="audio/mp3", autoplay=True)
else:
    st.info("🗣️ **AI Voice Assistant:** Standing by. No active voice broadcasts.")

# =========================================================
# METRICS ROW 1
# =========================================================
m1, m2, m3, m4, m5, m6 = st.columns(6)
m1.metric("Moisture",      f"{round(latest.get('soil_pct', 0), 1)}%")
m2.metric("Temp (°C)",     round(latest.get("temp", 0), 1))
m3.metric("Humidity",      f"{round(latest.get('humidity', 0), 1)}%")
m4.metric("Rain Sensor",   "☔ YES" if latest.get("rain", 0) == 1 else "☀ NO")
m5.metric("Rain Forecast", "🌧 YES" if rain_forecast_val == 1 else "☀ NO")
m6.metric("Pump Status",   "🔴 ACTIVE" if latest.get("decision", 0) == 1 else "🟢 STANDBY")

st.markdown("<br>", unsafe_allow_html=True)

# =========================================================
# METRICS ROW 2
# =========================================================
s1, s2, s3, s4, s5, s6 = st.columns(6)
s1.metric("Soil Raw Value",      int(float(latest.get("soil", 0) or 0)))
s2.metric("AI Threshold",        int(float(latest.get("adaptive_threshold", 2500) or 2500)))
s3.metric("Pump Activations",    int(df["pump_count"].max()) if "pump_count" in df else 0)
s4.metric("Total Pump Time(ms)", f"{int(latest.get('pump_time', 0)):,}")
s5.metric("Dose Factor",         f"{dose_val*100:.0f}%")
s6.metric("Est. Water Used(ml)", f"{int(latest.get('water_ml', 0)):,}")

st.divider()

# =========================================================
# GAUGE + STATUS + AI CHART
# =========================================================
col_gauge, col_status, col_ai_chart = st.columns([1, 1, 2])

with col_gauge:
    st.markdown("### 🌱 Real-time Moisture")
    soil_pct_val = float(latest.get("soil_pct", 0))
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=soil_pct_val,
        number={"suffix": "%", "font": {"color": "#4ade80", "size": 36, "family": "Inter"}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#4ade80"},
            "bar":  {"color": "#4ade80"},
            "bgcolor": "#0d1a0d",
            "bordercolor": "#1a3a1a",
            "steps": [
                {"range": [0,  30],  "color": "#ef4444"},
                {"range": [30, 60],  "color": "#eab308"},
                {"range": [60, 100], "color": "#22c55e"}
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

    if rain_forecast_val == 1:
        st.warning("🌧 Weather AI: RAIN FORECAST")
    else:
        st.success("☀ Weather AI: CLEAR SKY")

    if len(df) > 0 and "decision" in df.columns:
        pump_on    = df["decision"].sum()
        efficiency = round(((len(df) - pump_on) / len(df)) * 100, 1)
        st.markdown(f"**Resource Efficiency:** `{efficiency}%`")

    if "dose_factor" in df.columns and len(df) > 0:
        avg_dose = round(df["dose_factor"].replace(0, 1.0).mean() * 100, 1)
        st.markdown(f"**Avg Dose Factor:** `{avg_dose}%`")

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
        if "rain_forecast" in df_ai.columns:
            rain_periods = df_ai[df_ai["rain_forecast"] == 1]
            if not rain_periods.empty:
                fig_ai.add_trace(go.Scatter(
                    x=df_ai.index, y=[3200] * len(df_ai),
                    fill=None, mode='lines',
                    line=dict(color='rgba(0,0,0,0)'), showlegend=False
                ))
                fig_ai.add_trace(go.Scatter(
                    x=df_ai.index,
                    y=[3200 if v == 1 else None for v in df_ai["rain_forecast"]],
                    fill='tozeroy', fillcolor='rgba(59,130,246,0.1)',
                    mode='none', name='Rain Forecast Period'
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
t1, t2, t3, t4, t5, t6 = st.columns(6)

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

with t6:
    st.caption("Dose Factor (%)")
    if "dose_factor" in df.columns and "time" in df.columns:
        st.line_chart(df.set_index("time")["dose_factor"] * 100, height=150, color="#a78bfa")

# =========================================================
# WATER USAGE TREND
# =========================================================
st.markdown("### 💧 Estimated Water Usage Over Time (ml)")
if "water_ml" in df.columns and "time" in df.columns:
    st.area_chart(df.set_index("time")["water_ml"], height=180, color="#22d3ee")

st.divider()

# =========================================================
# ADDITION 1: WATER SAVINGS ANALYSIS (runs live in dashboard)
# =========================================================
st.markdown("### 💰 Water Savings Analysis — Your System vs Traditional Fixed Threshold")

FIXED_THRESHOLD   = 2500
BASE_PUMP_MS      = 8000
FLOW_RATE_ML_PER_MS = 0.05

if len(df) >= 2 and "soil" in df.columns and "dose_factor" in df.columns:

    # Simulate what a fixed threshold system would have used
    def fixed_water_per_row(row):
        if row.get("rain", 0) == 1:
            return 0
        if row.get("soil", 0) >= FIXED_THRESHOLD:
            return BASE_PUMP_MS * FLOW_RATE_ML_PER_MS
        return 0

    df_savings = df.copy()
    df_savings["fixed_water"] = df_savings.apply(fixed_water_per_row, axis=1)
    df_savings["your_water"]  = (
        df_savings["dose_factor"] * BASE_PUMP_MS * FLOW_RATE_ML_PER_MS * df_savings["decision"]
    )
    df_savings["fixed_cumulative"] = df_savings["fixed_water"].cumsum()
    df_savings["your_cumulative"]  = df_savings["your_water"].cumsum()

    total_fixed  = df_savings["fixed_cumulative"].iloc[-1]
    total_yours  = df_savings["your_cumulative"].iloc[-1]
    total_saved  = max(total_fixed - total_yours, 0)
    pct_saved    = round((total_saved / total_fixed * 100), 1) if total_fixed > 0 else 0.0
    avg_dose     = round(df_savings[df_savings["dose_factor"] > 0]["dose_factor"].mean() * 100, 1)

    # Savings banner
    st.markdown(
        f'<div class="savings-banner">💰 WATER SAVINGS RESULT — Your confidence-weighted system saved '
        f'<b>{total_saved:.0f} ml ({pct_saved}%)</b> compared to a traditional fixed-threshold system '
        f'over {len(df)} data points. Average dose factor: <b>{avg_dose}%</b>.</div>',
        unsafe_allow_html=True
    )

    # Savings metrics row
    w1, w2, w3, w4 = st.columns(4)
    w1.metric("Fixed System Would Use", f"{total_fixed:.0f} ml")
    w2.metric("Your System Used",        f"{total_yours:.0f} ml")
    w3.metric("Total Water Saved",       f"{total_saved:.0f} ml")
    w4.metric("Savings %",               f"{pct_saved}%")

    st.markdown("<br>", unsafe_allow_html=True)

    # Cumulative comparison chart
    if "time" in df_savings.columns:
        fig_savings = go.Figure()
        fig_savings.add_trace(go.Scatter(
            x=df_savings["time"], y=df_savings["fixed_cumulative"],
            mode='lines', name='Fixed Threshold System (Traditional)',
            line=dict(color='#ef4444', width=2)
        ))
        fig_savings.add_trace(go.Scatter(
            x=df_savings["time"], y=df_savings["your_cumulative"],
            mode='lines', name='Your System (Confidence-Weighted)',
            line=dict(color='#22c55e', width=2),
            fill='tonexty', fillcolor='rgba(34,197,94,0.1)'
        ))
        fig_savings.update_layout(
            height=300,
            title=dict(
                text=f"Cumulative Water Usage Comparison — {pct_saved}% Savings Achieved",
                font=dict(color="#4ade80", size=13)
            ),
            margin=dict(t=40, b=10, l=0, r=0),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis=dict(showgrid=False, showticklabels=False),
            yaxis=dict(gridcolor="#1a3a1a", zeroline=False, title="Water Used (ml)"),
            font=dict(color="#8bba8b")
        )
        st.plotly_chart(fig_savings, use_container_width=True)

    # Dose factor vs rain probability scatter
    if "rain_probability" in df_savings.columns:
        fig_scatter = go.Figure()
        fig_scatter.add_trace(go.Scatter(
            x=df_savings["rain_probability"],
            y=df_savings["dose_factor"] * 100,
            mode='markers',
            marker=dict(color='#a78bfa', size=6, opacity=0.6),
            name='Rain Prob vs Dose Factor'
        ))
        fig_scatter.update_layout(
            height=250,
            title=dict(
                text="Rain Probability vs Dose Factor (System Intelligence Proof)",
                font=dict(color="#4ade80", size=12)
            ),
            margin=dict(t=40, b=10, l=0, r=0),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(
                title="Rain Probability (0=No Rain, 1=Certain Rain)",
                gridcolor="#1a3a1a", color="#8bba8b"
            ),
            yaxis=dict(
                title="Dose Factor (%)",
                gridcolor="#1a3a1a", color="#8bba8b"
            ),
            font=dict(color="#8bba8b")
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

else:
    st.info("⏳ Collecting data for water savings analysis... needs at least 2 data points.")

# ---------------- FOOTER ----------------
st.markdown("---")
st.markdown(
    '<p style="text-align:center; color:#2d5a2d; font-size:0.7rem; letter-spacing:0.1em;">'
    '⚡ EDGE AIoT SMART IRRIGATION &nbsp;|&nbsp; REAL-TIME MONITORING &nbsp;|&nbsp; '
    'IEEE RESEARCH PROJECT &nbsp;|&nbsp; Bengaluru, India</p>',
    unsafe_allow_html=True
)