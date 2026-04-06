import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime, timedelta
import pytz
from streamlit_autorefresh import st_autorefresh 
from emojis import get_emoji, RIDES_DLP, RIDES_DAW
from config import PARK_OPENING, DLP_CLOSING, DAW_CLOSING, EMT_OPENING
from special_hours import ANTICIPATED_CLOSINGS, FANTASYLAND_EARLY_CLOSE, EMT_EARLY_OPEN

# --- CONFIGURATION ---
st.set_page_config(page_title="Disney Live Board", page_icon="🏰", layout="wide")

# --- STYLE CSS (Tableaux Modernes) ---
st.markdown("""
<style>
    .land-header {
        background: linear-gradient(90deg, #1e293b 0%, #334155 100%);
        color: #f8fafc;
        padding: 10px 20px;
        border-radius: 12px;
        margin: 25px 0 15px 0;
        font-size: 20px;
        font-weight: 700;
        border-left: 5px solid #3b82f6;
    }
    .ride-container {
        background: #1e212b;
        border: 1px solid #2d313d;
        border-radius: 12px;
        padding: 12px;
        margin-bottom: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .wait-box {
        min-width: 60px;
        height: 50px;
        border-radius: 10px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        color: white;
    }
    .status-tag {
        font-size: 10px;
        padding: 2px 8px;
        border-radius: 20px;
        text-transform: uppercase;
        margin-top: 4px;
        background: rgba(0,0,0,0.2);
    }
</style>
""", unsafe_allow_html=True)

# --- LOGIQUE DE DONNÉES ---
paris_tz = pytz.timezone('Europe/Paris')
st_autorefresh(interval=60000, key="datarefresh")
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

maintenant = datetime.now(paris_tz)
heure_actuelle = maintenant.time()

try:
    resp_live = supabase.table("disney_live").select("*").execute()
    df_live = pd.DataFrame(resp_live.data)
    resp_status = supabase.table("daily_status").select("*").execute()
    status_map = {item['ride_name']: item for item in resp_status.data}
    resp_101 = supabase.table("logs_101").select("*").execute() # Pour les durées de pannes
    all_pannes = resp_101.data
except:
    st.error("Erreur de connexion aux serveurs.")
    st.stop()

# --- DÉFINITION DES LANDS ---
lands_structure = {
    "🏰 Disneyland Park": {
        "Main Street U.S.A": ["Horse-Drawn Streetcars", "Main Street Vehicles", "Disneyland Railroad Main Street Station"],
        "Frontierland": ["Big Thunder Mountain", "Phantom Manor", "Thunder Mesa Riverboat Landing", "Rustler Roundup Shootin' Gallery"],
        "Adventureland": ["Pirates of the Caribbean", "Indiana Jones", "La Cabane des Robinson", "Le Passage Enchanté d'Aladdin"],
        "Fantasyland": ["It's a small world", "Peter Pan's Flight", "Pinocchio", "Snow White", "Dumbo", "Mad Hatter's Tea Cups", "Casey Jr.", "Le Pays des Contes de Fées", "Alice's Curious Labyrinth"],
        "Discoveryland": ["Star Wars Hyperspace Mountain", "Star Tours", "Buzz Lightyear Laser Blast", "Orbitron", "Autopia", "Mickey's PhilharMagic"]
    },
    "🎬 Walt Disney Studios": {
        "Avengers Campus": ["Avengers Assemble: Flight Force", "Spider-Man W.E.B. Adventure"],
        "Worlds of Pixar": ["Crush's Coaster", "Ratatouille", "RC Racer", "Toy Soldiers Parachute Drop", "Slinky Dog Zigzag Spin", "Cars Road Trip", "Cars Quatre Roues Rallye"],
        "Production Courtyard": ["The Twilight Zone Tower of Terror"],
        "Adventure Way": ["Raiponce Tangled Spin"]
    }
}

# --- FONCTION D'AFFICHAGE D'UNE ATTRACTION ---
def render_ride(ride_name):
    ride_data = df_live[df_live['ride_name'] == ride_name]
    if ride_data.empty: return
    
    row = ride_data.iloc[0]
    info = status_map.get(ride_name, {})
    
    # Logique Status
    is_daw = any(a.lower() in ride_name.lower() for a in RIDES_DAW)
    h_o = EMT_OPENING if ride_name in EMT_EARLY_OPEN else PARK_OPENING
    h_f = DAW_CLOSING if is_daw else DLP_CLOSING
    if ride_name in ANTICIPATED_CLOSINGS: h_f = ANTICIPATED_CLOSINGS[ride_name]
    
    is_open = row['is_open']
    wait_time = int(row['wait_time'])
    
    # Détermination couleur et label
    rehab = not info.get('opened_yesterday', True) and not info.get('has_opened_today', False) and not is_open
    if is_open and wait_time > 0: rehab = False

    if rehab:
        color, label, wait_txt = "#6b7280", "REHAB", "TRVX"
    elif heure_actuelle >= h_f and not is_open:
        color, label, wait_txt = "#991b1b", "FERMÉ", "FIN"
    elif heure_actuelle < h_o and not is_open:
        color, label, wait_txt = "#3b82f6", "ATTENTE", "SOON"
    elif not is_open:
        color, label, wait_txt = "#f59e0b", "INCIDENT", "101"
    else:
        color = "#10b981" if wait_time <= 20 else ("#f59e0b" if wait_time <= 45 else "#ef4444")
        label, wait_txt = "OUVERT", f"{wait_time}"

    st.markdown(f"""
        <div class="ride-container">
            <div style="display:flex; align-items:center; gap:12px;">
                <span style="font-size:20px;">{get_emoji(ride_name)}</span>
                <div>
                    <div class="ride-main-name">{ride_name}</div>
                    <div style="font-size:10px; color:#94a3b8;">{label}</div>
                </div>
            </div>
            <div class="wait-box" style="background:{color};">
                <div style="font-size:18px;">{wait_txt}</div>
                <div style="font-size:8px; opacity:0.8;">{"MIN" if wait_txt.isdigit() else ""}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

# --- CORPS DU TABLEAU ---
st.title("🏰 Live Attractions Board")
st.caption(f"Dernière mise à jour : {derniere_maj} | Rafraîchissement automatique (1 min)")

# Séparation en deux colonnes pour les deux parcs
col_dlp, col_daw = st.columns(2)

with col_dlp:
    st.markdown('<div class="land-header">🏰 DISNEYLAND PARK</div>', unsafe_allow_html=True)
    for land, rides in lands_structure["🏰 Disneyland Park"].items():
        with st.expander(f"📍 {land}", expanded=True):
            for r in rides:
                render_ride(r)

with col_daw:
    st.markdown('<div class="land-header">🎬 WALT DISNEY STUDIOS</div>', unsafe_allow_html=True)
    for land, rides in lands_structure["🎬 Walt Disney Studios"].items():
        with st.expander(f"📍 {land}", expanded=True):
            for r in rides:
                render_ride(r)

st.caption("Disney Wait Time Tool | Dashboard v3.1")
