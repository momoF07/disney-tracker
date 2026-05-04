import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime, time
import pytz

# --- INITIALISATION & CONNEXION ---
st.set_page_config(page_title="Disney Tracker Pro", layout="wide", initial_sidebar_state="collapsed")

if "bypass_maintenance" not in st.session_state:
    st.session_state.bypass_maintenance = False

MAINTENANCE_MODE = False 
if MAINTENANCE_MODE and not st.session_state.bypass_maintenance:
    from maintenance import show_maintenance
    show_maintenance()

@st.cache_resource
def init_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_supabase()
paris_tz = pytz.timezone('Europe/Paris')
maintenant = datetime.now(paris_tz)

# --- 1. BLOC INFOS (Météo, Horaires, Spectacles) ---
st.title("🏰 Disney Live Control Center")

# On crée des sous-colonnes juste pour les petites infos du haut
info_cols = st.columns(3)

with info_cols[0]:
    # Météo avec Alerte Orage
    meteo = {"temp": 18, "condition": "Orage"} # Exemple API
    orage_alerte = "⚡ ALERTE ORAGE : Attractions extérieures fermées" if meteo["condition"] == "Orage" else "🌤️ Météo Clémente"
    st.metric("Météo", f"{meteo['temp']}°C", delta=orage_alerte, delta_color="inverse" if meteo["condition"] == "Orage" else "normal")

with info_cols[1]:
    # Horaires Parcs
    st.metric("Horaires DLP", "09:30 - 21:00", delta="EMT: 08:30")

with info_cols[2]:
    # Prochain Spectacle
    st.metric("Prochain Show", "Disney Illuminations", delta="À 21:00")

st.write("---")

# --- 2. BLOC TEMPS D'ATTENTE (Par Land) ---
st.header("🎢 Temps d'Attente")

# Exemple de filtre par Parc (Tabs)
tab1, tab2 = st.tabs(["Disneyland Park", "Disney Adventure World"])

with tab1:
    # Ici on bouclera sur PARKS_DATA["Disneyland Park"]
    # land_cols = st.columns(3) ... etc.
    st.info("Les cartes du Disneyland Park s'afficheront ici par zone.")

with tab2:
    st.info("Les cartes de Disney Adventure World s'afficheront ici.")

st.write("---")

# --- 3. BLOC FLUX D'ACTIVITÉS (Historique récent) ---
st.header("🚨 Flux d'Activités")

# Simulation de flux
flux_data = [
    {"time": "14:20", "event": "✅ Réouverture", "ride": "Big Thunder Mountain", "style": "green"},
    {"time": "14:05", "event": "⚠️ Interruption", "ride": "Star Wars Hyperspace Mountain", "style": "orange"},
]

for item in flux_data:
    st.markdown(f"""
        <div style="background: rgba(255,255,255,0.05); padding: 10px; border-radius: 10px; border-left: 20px solid {item['style']}; margin-bottom: 10px;">
            <small style="color: #64748b;">{item['time']}</small> | <b>{item['event']}</b> : {item['ride']}
        </div>
    """, unsafe_allow_html=True)

st.write("---")

# --- 4. BLOC ANALYSE & STATS (Le mois) ---
st.header("📊 Statistiques du Mois")
st.caption("Données basées sur les 30 derniers jours")

stat_cols = st.columns(3)
with stat_cols[0]:
    st.metric("Interruptions totales", "42", delta="+5% vs mois dernier")
with stat_cols[1]:
    st.metric("Durée moyenne 101", "24 min", delta="-2 min")
with stat_cols[2]:
    st.metric("Attente moy. globale", "35 min")

# Graphique d'activité
st.area_chart(pd.DataFrame([10, 15, 8, 12, 20, 14], columns=["Pannes"]), height=200)