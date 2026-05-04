import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
import pytz

# --- CONFIGURATION & DONNÉES DE RÉFÉRENCE ---
st.set_page_config(page_title="Disney Tracker Pro", layout="wide", initial_sidebar_state="collapsed")

# Simulation des données de structure (À lier à ta table rides_info plus tard)
PARKS_DATA = {
    "Disneyland Park": {
        "Main Street U.S.A": ["Railroad"],
        "Fantasyland": ["Peter Pan", "it's a small world"],
        "Adventureland": ["Pirates", "Indy"],
        "Frontierland": ["BTM", "Phantom Manor"],
        "Discoveryland": ["Space Mountain", "Star Tours"]
    },
    "Disney Adventure World": {
        "World of Pixar": ["Crush's Coaster", "Ratatouille"],
        "Avengers Campus": ["Spider-Man", "Iron Man"],
        "Production Courtyard": ["Tower of Terror"]
    }
}

# Liste plate pour le sélecteur par attraction
ALL_RIDES_LIST = [ride for park in PARKS_DATA.values() for land in park.values() for ride in land]

# --- CONNEXION SUPABASE ---
@st.cache_resource
def init_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

# supabase = init_supabase() # Activé une fois les secrets configurés

# --- HEADER & INFOS ---
st.title("🏰 Disney Live Control Center")

info_cols = st.columns(3)
with info_cols[0]:
    meteo = {"temp": 18, "condition": "Orage"} 
    orage_alerte = "⚡ ALERTE ORAGE" if meteo["condition"] == "Orage" else "🌤️ Météo Clémente"
    st.metric("Météo", f"{meteo['temp']}°C", delta=orage_alerte, delta_color="inverse" if meteo["condition"] == "Orage" else "normal")

with info_cols[1]:
    st.metric("Horaires DLP", "09:30 - 21:00", delta="EMT: 08:30")

with info_cols[2]:
    st.metric("Prochain Show", "Disney Illuminations", delta="À 21:00")

st.write("---")

# --- TEMPS D'ATTENTE ---
st.header("🎢 Temps d'Attente")
tab1, tab2 = st.tabs(["Disneyland Park", "Disney Adventure World"])

with tab1:
    st.info("Les cartes du Disneyland Park s'afficheront ici par zone.")
with tab2:
    st.info("Les cartes de Disney Adventure World s'afficheront ici.")

st.write("---")

# --- FLUX D'ACTIVITÉS ---
st.header("🚨 Flux d'Activités")
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

# --- 4. BLOC ANALYSE & STATS ---
st.header("📊 Analyse de Performance")

# Sélecteurs de granularité
col_scope, col_target = st.columns(2)

with col_scope:
    scope = st.selectbox(
        "Niveau d'analyse", 
        ["Global (2 Parcs)", "Disneyland Park", "Disney Adventure World", "Par Land", "Par Attraction"]
    )

# Logique dynamique pour le deuxième sélecteur
target_options = []
if scope == "Par Land":
    target_options = list(PARKS_DATA["Disneyland Park"].keys()) + list(PARKS_DATA["Disney Adventure World"].keys())
elif scope == "Par Attraction":
    target_options = ALL_RIDES_LIST

with col_target:
    if target_options:
        target_selection = st.selectbox(f"Choisir l'élément", target_options)
    else:
        st.info("Analyse groupée active : " + scope)

# Affichage des Metrics
st.markdown("#### Indicateurs clés (30 derniers jours)")
m_cols = st.columns(3)

with m_cols[0]:
    st.metric("Total Interruptions", "128", delta="-12% (Mois dernier)")
    
with m_cols[1]:
    st.metric("Moyenne 101", "28 min", delta="Stable")
    
with m_cols[2]:
    st.metric("Attente Moyenne", "42 min", delta="+5 min")

# Graphique Temporel
st.markdown(f"**Évolution des incidents : {scope if not target_options else target_selection}**")
st.area_chart(pd.DataFrame([2, 5, 1, 4, 3, 6, 4], columns=["Incidents"]), height=200)