import streamlit as st
import pandas as pd
import pytz
import config as cfg # Utilise ton fichierEmojis/PARKS_DATA
from datetime import datetime, timezone
from data_manager import init_supabase, get_live_wait_times, get_ride_history, get_weather
from streamlit_autorefresh import st_autorefresh

# --- CONFIGURATION ---
st.set_page_config(page_title="Disney Tracker Pro v2", layout="wide")
st_autorefresh(interval=2 * 60 * 1000, key="refresh") # Auto-refresh 2min
supabase = init_supabase()
paris_tz = pytz.timezone("Europe/Paris")
now_p = datetime.now(paris_tz)

# --- SIDEBAR (FILTRES) ---
with st.sidebar:
    st.header("⚙️ Paramètres")
    selected_park = st.selectbox("Choisir le Parc", ["Disneyland Park", "Disney Adventure World"])
    lands = list(cfg.PARKS_DATA[selected_park].keys())
    selected_lands = st.multiselect("Filtrer les Zones", lands, default=lands)
    show_only_open = st.toggle("Uniquement Ouvert", value=False)

# --- HEADER DATA ---
weather = get_weather()
live_data = get_live_wait_times(supabase)

# --- TOP BAR ---
st.title("🏰 Disney Live Control Center")
c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Météo", f"{weather['temp']}°C", weather['status'])
with c2:
    # Affluence globale basée sur la moyenne des attentes
    avg = int(sum(d['wait_time'] for d in live_data.values() if d['is_open']) / len(live_data)) if live_data else 0
    st.metric("Affluence Globale", f"{avg} min", "Stable" if avg < 30 else "Chargé")
with c3:
    st.metric("Dernier Scan", now_p.strftime("%H:%M"))

st.divider()

# --- RENDU DES CARTES ---
for land in selected_lands:
    rides = cfg.PARKS_DATA[selected_park][land]
    st.subheader(f"📍 {land}")
    cols = st.columns(4)
    for i, r_name in enumerate(rides):
        data = live_data.get(r_name)
        if not data or (show_only_open and not data['is_open']): continue
        
        with cols[i % 4]:
            with st.container(border=True):
                st.markdown(f"**{r_name}**")
                if data['is_open']:
                    wait = data['wait_time']
                    st.markdown(f"### {wait} <small>min</small>", unsafe_allow_html=True)
                    st.progress(min(wait/120, 1.0))
                    with st.popover("📈 Historique"):
                        h_df = get_ride_history(supabase, r_name)
                        if not h_df.empty: st.line_chart(h_df.set_index("heure")["attente"])
                else:
                    st.markdown("### 🔒 Fermé")