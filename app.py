# app.py
import streamlit as st
import pandas as pd
import config as cfg
import pytz
from datetime import datetime, timezone
from ui_components import render_metric_row, render_activity_item
from data_manager import * # Importe init_supabase, get_park_schedule, etc.
from streamlit_autorefresh import st_autorefresh

# --- CONFIGURATION ET STYLE ---
st.set_page_config(page_title="Disney Live Board", page_icon="🏰", layout="wide")
st_autorefresh(interval=60000, key="datarefresh") # Refresh chaque minute[cite: 5]

st.markdown("""
    <style>
    .stApp { background: radial-gradient(circle at top right, #1e293b, #0f172a); }
    h1, h2 { background: linear-gradient(120deg, #4facfe 0%, #00f2fe 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800 !important; }
    .status-pill { padding: 3px 12px; border-radius: 20px; font-size: 11px; font-weight: bold; float: right; border: 1px solid; }
    .pill-open { background: rgba(46, 204, 113, 0.15); color: #2ecc71; border-color: #2ecc71; }
    .pill-down { background: rgba(231, 76, 60, 0.15); color: #e74c3c; border-color: #e74c3c; }
    </style>
""", unsafe_allow_html=True)

# --- INITIALISATION ---
supabase = init_supabase()
paris_tz = pytz.timezone("Europe/Paris")
now_p = datetime.now(paris_tz)
today_date = now_p.date().isoformat()

# --- RÉCUPÉRATION DATA ---
live_data = get_live_wait_times(supabase)
weather_data = get_weather()
sched_data = get_park_schedule(supabase, today_date) # Plus d'erreur NameError ici[cite: 5]

# --- HEADER DYNAMIQUE ---
st.title("✨ Disney Live Board")

h_display = "Indisponible"
if sched_data:
    # On cherche l'horaire de Disneyland Park (DLP)[cite: 5]
    s = next((item for item in sched_data if item["park_id"] == "DLP"), None)
    if s:
        o = pd.to_datetime(s['opening_time']).astimezone(paris_tz).strftime("%H:%M")
        c = pd.to_datetime(s['closing_time']).astimezone(paris_tz).strftime("%H:%M")
        h_display = f"{o} - {c}"

render_metric_row(weather_data, h_display, {"name": "Disney Illuminations", "time": "21:30"})

# --- FILTRES ET TRI ---
c1, c2, c3 = st.columns([1, 1, 1.5])
with c1:
    if st.button("🔄 Actualiser", use_container_width=True): st.rerun()
with c3:
    sort_mode = st.segmented_control("Trier par", ["🔠 Nom", "⏳ Attente", "⚠️ Incidents"], default="🔠 Nom")

st.divider()

# --- RENDU DES ATTRACTIONS ---
tabs = st.tabs(["🏰 Disneyland Park", "🎬 Adventure World"])

def render_park_section(park_key):
    all_rides = [r for land in cfg.PARKS_DATA[park_key].values() for r in land]
    
    # Logique de tri[cite: 5]
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
        for i, ride_name in enumerate(current_rides):
            data = live_data.get(ride_name)
            with cols[i % 4]:
                with st.container(border=True):
                    if data:
                        is_open = data['is_open']
                        pill_class = "pill-open" if is_open else "pill-down"
                        st.markdown(f'<span class="status-pill {pill_class}">{"OUVERT" if is_open else "INCIDENT"}</span>', unsafe_allow_html=True)
                        st.markdown(f"**{cfg.get_emoji(ride_name)} {ride_name}**")
                        
                        if is_open:
                            wait = data['wait_time']
                            color = "#2ecc71" if wait < 20 else "#f1c40f" if wait < 50 else "#e74c3c"
                            c_w, c_p = st.columns([2, 1])
                            c_w.markdown(f"<h3 style='color:{color}; margin:0;'>{wait} min</h3>", unsafe_allow_html=True)
                            with c_p:
                                with st.popover("📈"):
                                    h_df = get_ride_history_24h(supabase, ride_name)
                                    if not h_df.empty: st.line_chart(h_df.set_index("heure")["attente"])
                        else:
                            st.markdown("<p style='color:#94a3b8; font-style:italic;'>Interruption technique</p>", unsafe_allow_html=True)

with tabs[0]: render_park_section("Disneyland Park")
with tabs[1]: render_park_section("Disney Adventure World")