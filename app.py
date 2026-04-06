import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime, timedelta
import pytz
from streamlit_autorefresh import st_autorefresh 
from emojis import get_emoji, RIDES_DLP, RIDES_DAW
from config import PARK_OPENING, DLP_CLOSING, DAW_CLOSING, EMT_OPENING
from special_hours import ANTICIPATED_CLOSINGS, FANTASYLAND_EARLY_CLOSE, EMT_EARLY_OPEN

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Disney Live Board", page_icon="🏰", layout="wide")

# --- STYLE CSS (Tableaux Modernes & Glassmorphism) ---
st.markdown("""
<style>
    .land-header {
        background: linear-gradient(90deg, #1e293b 0%, #334155 100%);
        color: #f8fafc;
        padding: 12px 20px;
        border-radius: 12px;
        margin: 20px 0 10px 0;
        font-size: 18px;
        font-weight: 700;
        border-left: 5px solid #4facfe;
    }
    .ride-container {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 10px 15px;
        margin-bottom: 6px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        transition: 0.2s;
    }
    .ride-container:hover {
        background: rgba(255, 255, 255, 0.06);
    }
    .ride-name-text {
        color: white;
        font-size: 14px;
        font-weight: 500;
    }
    .wait-box {
        min-width: 55px;
        height: 45px;
        border-radius: 10px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        color: white;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    }
    .status-sub {
        font-size: 9px;
        color: #94a3b8;
        text-transform: uppercase;
        margin-top: 2px;
    }
</style>
""", unsafe_allow_html=True)

# --- INITIALISATION & AUTO-REFRESH ---
paris_tz = pytz.timezone('Europe/Paris')
st_autorefresh(interval=60000, key="datarefresh")
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

# --- RÉCUPÉRATION DES DONNÉES (Sécurisée) ---
maintenant = datetime.now(paris_tz)
heure_actuelle = maintenant.time()
derniere_maj = "--:--:--"
df_live = pd.DataFrame()
status_map = {}

try:
    resp_live = supabase.table("disney_live").select("*").execute()
    df_live = pd.DataFrame(resp_live.data)
    
    if not df_live.empty:
        derniere_maj = pd.to_datetime(df_live['updated_at']).dt.tz_convert('Europe/Paris').max().strftime("%H:%M:%S")
    
    resp_status = supabase.table("daily_status").select("*").execute()
    status_map = {item['ride_name']: item for item in resp_status.data} if resp_status.data else {}
    
except Exception as e:
    st.error(f"Connexion impossible : {e}")

# --- STRUCTURE DES LANDS ---
lands_structure = {
    "🏰 Disneyland Park": {
        "Main Street U.S.A": ["Horse-Drawn Streetcars", "Main Street Vehicles", "Disneyland Railroad Main Street Station"],
        "Frontierland": ["Big Thunder Mountain", "Phantom Manor", "Thunder Mesa Riverboat Landing", "Rustler Roundup Shootin' Gallery"],
        "Adventureland": ["Pirates of the Caribbean", "Indiana Jones and the Temple of Peril", "La Cabane des Robinson", "Le Passage Enchanté d'Aladdin", "Pirate Galleon"],
        "Fantasyland": ["It's a small world", "Peter Pan's Flight", "Mad Hatter's Tea Cups", "Casey Jr. - le Petit Train du Cirque", "Le Pays des Contes de Fées", "Dumbo the Flying Elephant", "Alice's Curious Labyrinth", "Les Voyages de Pinocchio", "Blanche-Neige et les Sept Nains", "Le Carrousel de Lancelot"],
        "Discoveryland": ["Star Wars Hyperspace Mountain", "Star Tours: l'Aventure Continue", "Buzz Lightyear Laser Blast", "Orbitron", "Autopia", "Mickey's PhilharMagic"]
    },
    "🎬 Walt Disney Studios": {
        "Avengers Campus": ["Avengers Assemble: Flight Force", "Spider-Man W.E.B. Adventure"],
        "Worlds of Pixar": ["Crush's Coaster", "Ratatouille: L'Aventure Totalement Toquée de Rémy", "RC Racer", "Toy Soldiers Parachute Drop", "Slinky Dog Zigzag Spin", "Cars Road Trip", "Cars Quatre Roues Rallye"],
        "Production Courtyard": ["The Twilight Zone Tower of Terror"],
        "Adventure Way": ["Raiponce Tangled Spin"]
    }
}

# --- FONCTION DE RENDU ---
def render_ride(ride_name):
    if df_live.empty: return
    ride_data = df_live[df_live['ride_name'] == ride_name]
    if ride_data.empty: return
    
    row = ride_data.iloc[0]
    info = status_map.get(ride_name, {})
    
    # Horaires
    is_daw = any(a.lower() in ride_name.lower() for a in RIDES_DAW)
    h_o = EMT_OPENING if ride_name in EMT_EARLY_OPEN else PARK_OPENING
    h_f = DAW_CLOSING if is_daw else DLP_CLOSING
    if ride_name in ANTICIPATED_CLOSINGS: h_f = ANTICIPATED_CLOSINGS[ride_name]
    
    # Logique de Statut
    is_open = row['is_open']
    wait_time = int(row['wait_time'])
    rehab = not info.get('opened_yesterday', True) and not info.get('has_opened_today', False) and not is_open
    if is_open and wait_time > 0: rehab = False

    if rehab:
        color, label, wait_txt = "#4b5563", "REHAB", "TRVX"
    elif heure_actuelle >= h_f and not is_open:
        color, label, wait_txt = "#7f1d1d", "FERMÉ", "FIN"
    elif heure_actuelle < h_o and not is_open:
        color, label, wait_txt = "#1e40af", "SOON", "⌛"
    elif not is_open:
        color, label, wait_txt = "#92400e", "PANNE", "101"
    else:
        # Couleurs dynamiques selon l'attente
        if wait_time <= 15: color = "#059669" # Vert foncé
        elif wait_time <= 40: color = "#d97706" # Orange
        else: color = "#dc2626" # Rouge
        label, wait_txt = "OUVERT", f"{wait_time}"

    st.markdown(f"""
        <div class="ride-container">
            <div style="display:flex; align-items:center; gap:10px;">
                <span style="font-size:18px;">{get_emoji(ride_name)}</span>
                <div>
                    <div class="ride-name-text">{ride_name}</div>
                    <div class="status-sub">{label}</div>
                </div>
            </div>
            <div class="wait-box" style="background:{color};">
                <div style="font-size:16px;">{wait_txt}</div>
                <div style="font-size:7px; opacity:0.8;">{"MIN" if wait_txt.isdigit() else ""}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

# --- AFFICHAGE DU DASHBOARD ---
st.title("🏰 Disneyland Paris Live Board")
st.caption(f"Dernière synchro API : {derniere_maj} | Actualisation auto : 60s")

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

st.write("---")
st.caption("Données temps réel - Dashboard v4.0")
