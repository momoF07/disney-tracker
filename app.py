import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
import pytz

# --- CONFIGURATION ---
st.set_page_config(page_title="Disney Tracker Pro", layout="wide")

# Initialisation Session & Maintenance
if "bypass_maintenance" not in st.session_state:
    st.session_state.bypass_maintenance = False

MAINTENANCE_MODE = False # À passer à True si besoin

if MAINTENANCE_MODE and not st.session_state.bypass_maintenance:
    from maintenance import show_maintenance
    show_maintenance()

# --- CONNEXION ---
@st.cache_resource
def init_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_supabase()

# --- INTERFACE PRINCIPALE ---
st.title("🏰 Disney Live Control Center")

# Layout principal en 3 colonnes
col_left, col_mid, col_right = st.columns([1, 2, 1.2], gap="medium")

with col_left:
    st.header("🚨 Flux")
    # Ici : Flux d'activités (dernières pannes/réouvertures)

with col_mid:
    st.header("🎢 Attractions")
    # Ici : Cartes temps d'attente filtrées par Land

with col_right:
    st.header("📊 Insights & Infos")
    # Ici : Météo, Spectacles et Stats du mois