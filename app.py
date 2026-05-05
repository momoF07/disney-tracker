import streamlit as st
import pandas as pd
import config as cfg
import pytz
from datetime import datetime
from ui_components import render_activity_item
from data_manager import *
from streamlit_autorefresh import st_autorefresh

# --- CONFIGURATION ---
st.set_page_config(page_title="Disney Live Board", page_icon="🏰", layout="wide")
st_autorefresh(interval=60000, key="datarefresh")
supabase = init_supabase()
paris_tz = pytz.timezone("Europe/Paris")
now_p = datetime.now(paris_tz)
today_str = now_p.date().isoformat()

# --- CSS MAGIQUE ---
st.markdown("""
    <style>
    .stApp { background: radial-gradient(circle at top right, #1e293b, #0f172a); }
    h1, h2, h3 { background: linear-gradient(120deg, #4facfe 0%, #00f2fe 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800 !important; }
    .status-pill { padding: 3px 10px; border-radius: 15px; font-size: 10px; font-weight: bold; float: right; border: 1px solid; }
    .pill-open { background: rgba(46, 204, 113, 0.15); color: #2ecc71; border-color: #2ecc71; }
    .pill-down { background: rgba(231, 76, 60, 0.15); color: #e74c3c; border-color: #e74c3c; }
    </style>
""", unsafe_allow_html=True)

# --- DATA RECOVERY ---
live_data = get_live_wait_times(supabase)
sched_data = get_park_schedule(supabase, today_str)
upcoming_shows = get_upcoming_shows(supabase)
weather = get_weather()

# --- HEADER (Horaires & Shows) ---
st.title("✨ Disney Live Control Center")

col_info1, col_info2, col_info3 = st.columns([1, 1.2, 1.5])

with col_info1:
    st.markdown("#### 🌤️ Météo & Parcs")
    st.write(f"🌡️ {weather['temp']}°C - {weather['status']}")
    # Affichage des horaires ligne par ligne
    for p_id in ["DLP", "DAW"]:
        s = next((item for item in sched_data if item["park_id"] == p_id), None)
        if s:
            o = pd.to_datetime(s['opening_time']).astimezone(paris_tz).strftime("%H:%M")
            c = pd.to_datetime(s['closing_time']).astimezone(paris_tz).strftime("%H:%M")
            label = "🏰 Disneyland" if p_id == "DLP" else "🎬 Adventure"
            st.write(f"**{label}** : {o} - {c}")

with col_info3:
    st.markdown("#### 🎭 Shows (Prochaines 2h)")
    if upcoming_shows:
        for s in upcoming_shows[:3]:
            t_show = pd.to_datetime(s['start_time']).astimezone(paris_tz).strftime("%H:%M")
            st.write(f"⌚ **{t_show}** - {s['show_name']}")
    else:
        st.write("Aucun show prévu prochainement.")

# --- FILTRES DE TRI ---
st.divider()
sort_mode = st.segmented_control(
    "Trier les attractions par :", 
    ["🔠 Nom", "⏳ Attente", "⚠️ Incidents"], 
    default="🔠 Nom"
)

# --- ATTRACTIONS ---
tabs = st.tabs(["🏰 Disneyland Park", "🎬 Adventure World"])

def render_park(park_key):
    # Logique de tri
    all_rides = [r for land in cfg.PARKS_DATA[park_key].values() for r in land]
    if sort_mode == "⏳ Attente":
        all_rides = sorted(all_rides, key=lambda x: live_data.get(x, {}).get('wait_time', 0), reverse=True)
    elif sort_mode == "⚠️ Incidents":
        all_rides = sorted(all_rides, key=lambda x: live_data.get(x, {}).get('is_open', True))
    else:
        all_rides = sorted(all_rides)

    for land, rides_in_land in cfg.PARKS_DATA[park_key].items():
        current_rides = [r for r in all_rides if r in rides_in_land]
        if not current_rides: continue
        st.markdown(f"#### 📍 {land}")
        cols = st.columns(4)
        for i, r_name in enumerate(current_rides):
            data = live_data.get(r_name)
            with cols[i % 4]:
                with st.container(border=True):
                    if data:
                        is_open = data['is_open']
                        pill_class = "pill-open" if is_open else "pill-down"
                        st.markdown(f'<span class="status-pill {pill_class}">{"OUVERT" if is_open else "INCIDENT"}</span>', unsafe_allow_html=True)
                        st.markdown(f"**{cfg.get_emoji(r_name)} {r_name}**")
                        if is_open:
                            wait = data['wait_time']
                            c_w, c_p = st.columns([2, 1])
                            c_w.markdown(f"### {wait} min")
                            with c_p:
                                with st.popover("📈"):
                                    h_df = get_ride_history_24h(supabase, r_name)
                                    if not h_df.empty: st.line_chart(h_df.set_index("heure")["attente"])
                        else:
                            st.write("🔧 Interruption technique")

with tabs[0]: render_park("Disneyland Park")
with tabs[1]: render_park("Disney Adventure World")

# --- FLUX D'ACTIVITÉS ---
st.divider()
st.header("🚨 Flux d'activités récents")
logs = get_recent_logs(supabase)
if logs:
    for l in logs:
        t_log = pd.to_datetime(l['start_time']).astimezone(paris_tz).strftime("%H:%M")
        event = "⚠️ Panne" if l['end_time'] is None else "✅ Réouverture"
        color = "#e74c3c" if l['end_time'] is None else "#2ecc71"
        render_activity_item(t_log, event, l['ride_name'], color)
else:
    st.write("Calme plat sur le parc.")