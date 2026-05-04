# app.py
import streamlit as st
import pandas as pd
import config as cfg  # Importation de ton config.py avec alias cfg
from ui_components import render_metric_row, render_activity_item
from data_manager import init_supabase

# Configuration de la page
st.set_page_config(page_title="Disney Tracker Pro", layout="wide", initial_sidebar_state="collapsed")

# Initialisation de la connexion (sera utilisée par data_manager plus tard)
# supabase = init_supabase() 

# --- 1. HEADER (Infos Météo / Horaires / Shows) ---
st.title("🏰 Disney Live Control Center")

# Simulation de données (À remplacer par des appels data_manager.py)
render_metric_row(
    {"temp": 18, "status": "Orage"}, 
    "09:30 - 21:00", 
    {"name": "Disney Illuminations", "time": "21:00"}
)
st.divider()

# --- 2. TEMPS D'ATTENTE (Structure par Onglets) ---
st.header("🎢 Temps d'Attente")
tab1, tab2 = st.tabs(["Disneyland Park", "Disney Adventure World"])

with tab1:
    # Ici, on pourra boucler sur cfg.PARKS_DATA["Disneyland Park"] pour créer les cartes
    st.info("Affichage des attractions du Disneyland Park (Filtrage par Land en cours...)")

with tab2:
    st.info("Affichage des attractions de Disney Adventure World...")

st.divider()

# --- 3. FLUX D'ACTIVITÉS (Journal des pannes/réouvertures) ---
st.header("🚨 Flux d'Activités")

# Simulation de flux (À remplacer par une requête sur tes logs Supabase)
render_activity_item("14:20", "✅ Réouverture", "Big Thunder Mountain", cfg.STYLES["green"])
render_activity_item("14:05", "⚠️ Interruption", "Star Wars Hyperspace Mountain", cfg.STYLES["orange"])

st.divider()

# --- 4. ANALYSE DE PERFORMANCE (Le bloc corrigé) ---
st.header("📊 Analyse de Performance")

# Sélecteurs de granularité
col_scope, col_target = st.columns(2)

with col_scope:
    scope = st.selectbox(
        "Niveau d'analyse", 
        ["Global (2 Parcs)", "Par Parc", "Par Land", "Par Attraction"]
    )

# Logique de sélection dynamique des cibles
target_options = []
target_selection = None

if scope == "Par Parc":
    target_options = ["DLP", "DAW"]
elif scope == "Par Land":
    # On fusionne les Lands des deux parcs provenant de PARKS_DATA
    lands_dlp = list(cfg.PARKS_DATA["Disneyland Park"].keys())
    lands_daw = list(cfg.PARKS_DATA["Disney Adventure World"].keys())
    target_options = lands_dlp + lands_daw
elif scope == "Par Attraction":
    target_options = cfg.ALL_RIDES_LIST

with col_target:
    if target_options:
        target_selection = st.selectbox(f"Choisir la cible ({scope})", target_options)

# --- RÉCUPÉRATION DES ATTRACTIONS CONCERNÉES ---
if scope == "Global (2 Parcs)":
    rides_to_analyze = cfg.ALL_RIDES_LIST
elif scope == "Par Attraction":
    rides_to_analyze = [target_selection] if target_selection else []
else:
    # On utilise ta fonction get_rides_by_zone de config.py
    # Elle gère les alias (DLP/DAW) et les noms de Lands
    rides_to_analyze = cfg.get_rides_by_zone(target_selection, cfg.ALL_RIDES_LIST)

# --- AFFICHAGE DES STATISTIQUES ---
if rides_to_analyze:
    st.caption(f"Analyse basée sur {len(rides_to_analyze)} attraction(s) : {', '.join(rides_to_analyze[:3])}...")
    
    m_cols = st.columns(3)
    # Remplacer les valeurs fixes par des requêtes agrégées via data_manager.py
    m_cols[0].metric("Total Interruptions", "128", delta="-12%")
    m_cols[1].metric("Moyenne Durée 101", "28 min", delta="Stable")
    m_cols[2].metric("Attente Moyenne", "42 min", delta="+5 min")

    # Graphique Temporel
    st.subheader(f"Évolution des incidents : {target_selection if target_selection else 'Global'}")
    # Simulation de données
    dummy_data = pd.DataFrame([2, 5, 1, 4, 3, 6, 2], columns=["Nombre de pannes"])
    st.area_chart(dummy_data, height=200, color="#5072ff")
else:
    st.warning("Sélectionnez une zone ou une attraction pour voir les statistiques.")