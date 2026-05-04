# app.py
import streamlit as st
import pandas as pd
from config import PARKS_DATA, ALL_RIDES_LIST
from ui_components import render_metric_row, render_activity_item
from data_manager import init_supabase

st.set_page_config(page_title="Disney Tracker Pro", layout="wide")

# --- 1. HEADER ---
st.title("🏰 Disney Live Control Center")
render_metric_row(
    {"temp": 18, "status": "Orage"}, 
    "09:30 - 21:00", 
    {"name": "Illuminations", "time": "21:00"}
)
st.divider()

# --- 2. TEMPS D'ATTENTE ---
st.header("🎢 Temps d'Attente")
tab1, tab2 = st.tabs(["Disneyland Park", "Disney Adventure World"])
# Utilisation de boucles via PARKS_DATA...

# --- 3. FLUX ---
st.header("🚨 Flux d'Activités")
render_activity_item("14:20", "✅ Réouverture", "Big Thunder Mountain", "green")

# --- 4. ANALYSE ---
st.header("📊 Analyse de Performance")
col_scope, col_target = st.columns(2)
scope = col_scope.selectbox("Niveau d'analyse", ["Global", "Par Land", "Par Attraction"])

# Logique de sélection dynamique
target_options = []
if scope == "Par Land":
    target_options = list(PARKS_DATA["Disneyland Park"].keys())
elif scope == "Par Attraction":
    target_options = ALL_RIDES_LIST

target = col_target.selectbox("Cible", target_options) if target_options else None

st.area_chart(pd.DataFrame([1, 3, 2, 5]), height=200)