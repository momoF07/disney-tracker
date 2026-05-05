import streamlit as st
import pandas as pd
import config as cfg
import pytz
import requests
from datetime import datetime, timezone, timedelta, time
from ui_components import render_metric_row, render_activity_item
from data_manager import *
from streamlit_autorefresh import st_autorefresh

# --- CONFIGURATION & STYLE ---
st.set_page_config(page_title="Disney Live Board", page_icon="🏰", layout="wide", initial_sidebar_state="collapsed")
st_autorefresh(interval=60000, key="datarefresh") # Refresh 1 min pour la précision

# Injection du CSS "Magique" (Inspiré de l'ancien styles.py)
st.markdown("""
    <style>
    .stApp { background: radial-gradient(circle at top right, #1e293b, #0f172a); }
    h1, h2 { background: linear-gradient(120deg, #4facfe 0%, #00f2fe 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800 !important; }
    
    /* Pills de statut */
    .status-pill { padding: 2px 10px; border-radius: 20px; font-size: 10px; font-weight: bold; float: right; }
    .pill-open { background: rgba(46, 204, 113, 0.2); color: #2ecc71; border: 1px solid #2ecc71; }
    .pill-down { background: rgba(231, 76, 60, 0.2); color: #e74c3c; border: 1px solid #e74c3c; }
    .pill-closed { background: rgba(148, 163, 184, 0.2); color: #94a3b8; border: 1px solid #94a3b8; }
    
    /* Cartes */
    div[data-testid="stVerticalBlock"] > div[style*="border: 1px solid"] {
        border: 1px solid rgba(255,255,255,0.05) !important;
        background: rgba(255,255,255,0.02) !important;
        transition: transform 0.2s ease-in-out, border 0.2s;
        border-radius: 15px !important;
    }
    div[data-testid="stVerticalBlock"] > div[style*="border: 1px solid"]:hover {
        transform: translateY(-5px);
        border: 1px solid #5072ff !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- INITIALISATION ---
supabase = init_supabase()
paris_tz = pytz.timezone('Europe/Paris')
maintenant = datetime.now(paris_tz)
heure_actuelle = maintenant.time()
today_date = maintenant.date().isoformat()

# --- RECUPERATION DATA ---
live_data = get_live_wait_times(supabase)
weather = get_weather()
sched_data = get_park_schedule(supabase, today_date)

# --- HEADER (Inspiré de render_api_info) ---
st.title("🏰 Disney Live Board")

# Récupération des horaires DLP pour le header
res_dlp = supabase.table("park_schedule").select("*").eq("park_id", "DLP").eq("date", today_date).execute()
h_display = "Indisponible"
if res_dlp.data:
    s = res_dlp.data[0]
    o = pd.to_datetime(s['opening_time']).astimezone(paris_tz).strftime("%H:%M")
    c = pd.to_datetime(s['closing_time']).astimezone(paris_tz).strftime("%H:%M")
    h_display = f"{o} - {c}"

render_metric_row(weather, h_display, {"name": "Illuminations", "time": "21:30"})

# --- ACTIONS & FILTRES (Segmented Control de l'ancien app.py) ---
c_btn1, c_btn2, c_btn3 = st.columns([1, 1, 2])
with c_btn1:
    if st.button('✨ Actualiser', use_container_width=True): st.rerun()

with c_btn3:
    sort_mode = st.segmented_control(
        "Trier par",
        options=["🔠 Nom", "⏳ Attente", "⚠️ Incidents"],
        default="🔠 Nom",
        key="sort_selector"
    )

st.divider()

# --- RENDU DES ATTRACTIONS ---
t1, t2 = st.tabs(["🏰 Disneyland Park", "🎬 Adventure World"])

def render_advanced_cards(park_key):
    # Logique de tri
    rides_list = []
    for land, rides in cfg.PARKS_DATA[park_key].items():
        rides_list.extend(rides)
    
    if sort_mode == "⏳ Attente":
        rides_list = sorted(rides_list, key=lambda x: live_data.get(x, {}).get('wait_time', 0), reverse=True)
    elif sort_mode == "⚠️ Incidents":
        rides_list = sorted(rides_list, key=lambda x: live_data.get(x, {}).get('is_open', True))
    else:
        rides_list = sorted(rides_list)

    # Affichage par Land (comme dans l'ancien système)
    for land, rides in cfg.PARKS_DATA[park_key].items():
        # Filtrer la liste triée pour ne garder que les rides de ce land
        land_rides = [r for r in rides_list if r in rides]
        if not land_rides: continue
        
        st.markdown(f"#### 📍 {land}")
        cols = st.columns(4)
        for i, r_name in enumerate(land_rides):
            data = live_data.get(r_name)
            with cols[i % 4]:
                with st.container(border=True):
                    if data:
                        is_open = data['is_open']
                        wait = data['wait_time']
                        
                        # Pills de statut (Style ancien)
                        pill_class = "pill-open" if is_open else "pill-down"
                        pill_text = "OUVERT" if is_open else "INCIDENT"
                        
                        # Check fermeture théorique (Logique special_hours)
                        # Ici on simplifie, mais tu peux réutiliser ta map ANTICIPATED_CLOSINGS
                        
                        st.markdown(f"""
                            <span class="status-pill {pill_class}">{pill_text}</span>
                            <div style='font-weight:bold; font-size:14px; margin-bottom:10px;'>{cfg.get_emoji(r_name)} {r_name}</div>
                        """, unsafe_allow_html=True)
                        
                        if is_open:
                            c1, c2 = st.columns([2, 1])
                            color = "#2ecc71" if wait < 20 else "#f1c40f" if wait < 50 else "#e74c3c"
                            c1.markdown(f"<h3 style='margin:0; color:{color};'>{wait} <small>min</small></h3>", unsafe_allow_html=True)
                            with c2:
                                with st.popover("📈"):
                                    h_df = get_ride_history_24h(supabase, r_name)
                                    if not h_df.empty: st.line_chart(h_df.set_index("heure")["attente"])
                            st.progress(min(wait/120, 1.0))
                        else:
                            st.markdown("<div style='color:#94a3b8; font-style:italic; margin-top:5px;'>Interruption technique</div>", unsafe_allow_html=True)
                    else:
                        st.caption("Indisponible")

with t1: render_advanced_cards("Disneyland Park")
with t2: render_advanced_cards("Disney Adventure World")

# --- FOOTER (Inspiré de l'ancien v4.0) ---
st.markdown(f"""
    <div style="text-align:right; color:#64748b; font-size:10px; margin-top:40px;">
        v5.0 Premium | Actualisé à {maintenant.strftime('%H:%M:%S')} | © Disney Wait Time
    </div>
""", unsafe_allow_html=True)