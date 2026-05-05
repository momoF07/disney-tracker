# app.py
import streamlit as st
import pandas as pd
import config as cfg
import pytz
from datetime import datetime, timezone
from ui_components import render_metric_row, render_activity_item
from data_manager import *
from streamlit_autorefresh import st_autorefresh

# --- CONFIGURATION & DESIGN ---
st.set_page_config(page_title="Disney Tracker Live", layout="wide")
st_autorefresh(interval=5 * 60 * 1000, key="datarefresh")

# Injection CSS pour le look "Magique"
st.markdown("""
    <style>
    /* Fond dégradé sombre */
    .stApp {
        background: radial-gradient(circle at top right, #1e293b, #0f172a);
    }
    
    /* Titres en dégradé */
    h1, h2, h3 {
        background: linear-gradient(120deg, #4facfe 0%, #00f2fe 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800 !important;
    }
    
    /* Style des onglets (Tabs) */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: rgba(255,255,255,0.05);
        border-radius: 10px 10px 0px 0px;
        color: white !important;
        border: none !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: rgba(80, 114, 255, 0.2) !important;
        border-bottom: 3px solid #5072ff !important;
    }
    
    /* Cartes d'attractions */
    div[data-testid="stVerticalBlock"] > div[style*="border: 1px solid"] {
        border: 1px solid rgba(255,255,255,0.1) !important;
        background: rgba(255,255,255,0.02) !important;
        transition: transform 0.2s ease-in-out;
    }
    div[data-testid="stVerticalBlock"] > div[style*="border: 1px solid"]:hover {
        transform: translateY(-5px);
        border: 1px solid #5072ff !important;
        background: rgba(80, 114, 255, 0.05) !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- LOGIQUE DE RÉCUPÉRATION (Même que précédemment) ---
supabase = init_supabase()
live_data = get_live_wait_times(supabase)
paris_tz = pytz.timezone("Europe/Paris")
now_p = datetime.now(paris_tz)
today = now_p.date().isoformat()

# (Récupération des horaires et du show ici...)
hours_display = "09:30 - 21:00" # Exemple dynamique normalement

# --- RENDER HEADER ---
st.title("✨ Disney Live Control Center")
render_metric_row({"temp": 12, "status": "Ciel Étoilé"}, hours_display, {"name": "Disney Illuminations", "time": "21:30"})

# --- RENDER ATTRACTIONS ---
st.markdown("## 🎢 Temps d'Attente Temps Réel")
t1, t2 = st.tabs(["🏰 Disneyland Park", "🎬 Adventure World"])

def render_styled_cards(park_key):
    for land, rides in cfg.PARKS_DATA[park_key].items():
        st.markdown(f"#### 📍 {land}")
        cols = st.columns(4)
        for i, r_name in enumerate(rides):
            data = live_data.get(r_name)
            with cols[i % 4]:
                with st.container(border=True):
                    if data:
                        # Emoji dynamique depuis config
                        emoji = cfg.get_emoji(r_name)
                        st.markdown(f"**{emoji} {r_name}**")
                        
                        if data['is_open']:
                            wait = data['wait_time']
                            # Couleur dynamique pour le chiffre
                            color = "#2ecc71" if wait <= 20 else "#f1c40f" if wait <= 50 else "#e74c3c"
                            
                            c1, c2 = st.columns([2, 1])
                            c1.markdown(f"<h2 style='color: {color}; margin:0;'>{wait} min</h2>", unsafe_allow_html=True)
                            with c2:
                                with st.popover("📈"):
                                    h_df = get_ride_history_24h(supabase, r_name)
                                    if not h_df.empty: 
                                        st.line_chart(h_df.set_index("heure")["attente"])
                            
                            # Barre de progression stylisée[cite: 5]
                            st.progress(min(wait/120, 1.0))
                        else:
                            st.markdown("<h3 style='color: #64748b;'>🔒 Fermé</h3>", unsafe_allow_html=True)
                    else:
                        st.caption("Données indisponibles")

with t1: render_styled_cards("Disneyland Park")
with t2: render_styled_cards("Disney Adventure World")

# --- ANALYSE & FLUX (Rendu stylisé) ---
st.divider()
st.header("📊 Analyse & Activité")
c_left, c_right = st.columns([2, 1])

with c_left:
    # Intégration de tes stats 30j ici[cite: 7]
    st.info("Historique des performances (30 derniers jours)")
    # (Graphique de tendance ici...)

with c_right:
    st.subheader("🚨 Flux Live")
    recent_logs = get_recent_logs(supabase, limit=5)
    for log in recent_logs:
        render_activity_item("21:45", "Interruption", log['ride_name'], "#e74c3c")