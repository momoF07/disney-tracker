import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime, timedelta, time, date
import pytz
import requests
import time as time_sleep
import random
from streamlit_autorefresh import st_autorefresh 
from emojis import get_emoji, get_rides_by_zone, RIDES_DLP, RIDES_DAW
from config import PARK_OPENING, DLP_CLOSING, DAW_CLOSING, EMT_OPENING
from special_hours import ANTICIPATED_CLOSINGS, FANTASYLAND_EARLY_CLOSE, EMT_EARLY_OPEN

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Disney Wait Time", page_icon="🏰", layout="centered")

# --- STYLE CSS GLOBAL & MAGIQUE ---
st.markdown("""
<style>
    /* Design des badges de la boucle d'affichage */
    .ride-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px; width: 100%; gap: 10px; }
    .ride-left-card { border-radius: 16px; padding: 10px 15px; display: flex; align-items: center; justify-content: space-between; flex-grow: 1; height: 68px; }
    .ride-info-meta { display: flex; align-items: center; gap: 12px; }
    .ride-titles { display: flex; flex-direction: column; }
    .ride-main-name { color: white; font-size: 14px; font-weight: 600; margin: 0; }
    .ride-sub-status { color: rgba(255,255,255,0.7); font-size: 11px; margin: 0; }
    .state-pill { background: rgba(0,0,0,0.3); color: white; font-size: 10px; font-weight: 700; padding: 2px 8px; border-radius: 20px; text-transform: uppercase; border: 1px solid rgba(255,255,255,0.1); }
    .ride-right-wait { min-width: 75px; height: 68px; border-radius: 16px; display: flex; flex-direction: column; align-items: center; justify-content: center; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .wait-val { font-size: 20px; font-weight: 800; line-height: 1; }
    .wait-unit { font-size: 10px; font-weight: 400; opacity: 0.8; }

    /* Couleurs de cartes */
    .card-green { background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.3); }
    .card-orange { background: rgba(245, 158, 11, 0.15); border: 1px solid rgba(245, 158, 11, 0.3); }
    .card-blue { background: rgba(59, 130, 246, 0.15); border: 1px solid rgba(59, 130, 246, 0.3); }
    .card-grey { background: rgba(107, 114, 128, 0.15); border: 1px solid rgba(107, 114, 128, 0.3); }
    .card-bordeaux { background: rgba(153, 27, 27, 0.15); border: 1px solid rgba(153, 27, 27, 0.3); }
    .bg-green { background: #10b981; }
    .bg-orange { background: #f59e0b; }
    .bg-blue { background: #3b82f6; }
    .bg-grey { background: #6b7280; }
    .bg-bordeaux { background: #991b1b; }

    /* Animations Magiques pour le Popover */
    @keyframes shine { to { background-position: 200% center; } }
    .magic-title {
        text-align: center;
        background: linear-gradient(120deg, #4facfe 0%, #00f2fe 50%, #4facfe 100%);
        background-size: 200% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800; font-size: 28px; margin-bottom: 25px;
        animation: shine 3s linear infinite;
    }
    .cat-badge-magic {
        padding: 8px 20px; border-radius: 50px; font-size: 14px; font-weight: 700;
        display: block; text-align: center; margin: 20px 0 10px 0; text-transform: uppercase;
    }
    .bg-blue-magic { background: linear-gradient(45deg, #4facfe, #00f2fe); color: white; }
    .bg-green-magic { background: linear-gradient(45deg, #43e97b, #38f9d7); color: white; }
    .bg-orange-magic { background: linear-gradient(45deg, #f9d423, #ff4e50); color: white; }
    .shortcut-card {
        background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px); border-radius: 15px; padding: 12px; margin-bottom: 10px; transition: 0.3s;
    }
    .shortcut-card:hover { transform: translateY(-3px); background: rgba(255, 255, 255, 0.08); }
</style>
""", unsafe_allow_html=True)

# --- INITIALISATION ---
st.title("🏰 Disney Wait Time")
paris_tz = pytz.timezone('Europe/Paris')
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = datetime.now(paris_tz).strftime("%H:%M:%S")

st_autorefresh(interval=60000, key="datarefresh")
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def trigger_github_action():
    REPO, WORKFLOW_ID, TOKEN = "momoF07/disney-tracker", "check.yml", st.secrets["GITHUB_TOKEN"]
    url = f"https://api.github.com/repos/{REPO}/actions/workflows/{WORKFLOW_ID}/dispatches"
    headers = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        res = requests.post(url, headers=headers, json={"ref": "main"})
        return res.status_code
    except: return 500

# --- DATA RECOVERY ---
maintenant = datetime.now(paris_tz)
heure_actuelle = maintenant.time()
heure_reset = maintenant.replace(hour=2, minute=30, second=0, microsecond=0)
debut_journee = heure_reset if maintenant >= heure_reset else heure_reset - timedelta(days=1)

try:
    resp_live = supabase.table("disney_live").select("*").execute()
    df_live = pd.DataFrame(resp_live.data)
    resp_status = supabase.table("daily_status").select("*").execute()
    status_map = {item['ride_name']: item for item in resp_status.data} if resp_status.data else {}
    resp_101 = supabase.table("logs_101").select("*").gte("start_time", debut_journee.isoformat()).execute()
    df_pannes_brutes = pd.DataFrame(resp_101.data)
    derniere_maj = pd.to_datetime(df_live['updated_at']).dt.tz_convert('Europe/Paris').max().strftime("%H:%M:%S") if not df_live.empty else "--:--:--"
except: st.error("Erreur base de données")

all_pannes = []
if not df_live.empty and not df_pannes_brutes.empty:
    for _, row in df_pannes_brutes.iterrows():
        d_p = pd.to_datetime(row['start_time']).astimezone(paris_tz)
        f_p = pd.to_datetime(row['end_time']).astimezone(paris_tz) if pd.notna(row['end_time']) else None
        all_pannes.append({"ride": row['ride_name'], "debut": d_p, "fin": f_p, "statut": "EN_COURS" if f_p is None else "TERMINEE", "duree": int((f_p - d_p).total_seconds() / 60) if f_p else 0})

# --- HEADER INFO ---
header_html = f"""
<div style="background:rgba(255,255,255,0.05); padding:12px; border-radius:15px; border-left:4px solid #4facfe; margin-bottom:15px;">
    <div style="display:flex; justify-content:space-between; width:100%;">
        <div><span style="color:#94a3b8; font-size:12px;">API:</span> <b style="color:white;">{derniere_maj}</b></div>
        <div><span style="color:#94a3b8; font-size:12px;">Refresh:</span> <b style="color:white;">{st.session_state.last_refresh}</b></div>
    </div>
</div>
"""
st.markdown(header_html, unsafe_allow_html=True)

col_btn1, col_btn2 = st.columns(2)
with col_btn1:
    if st.button('✨ Actualiser', use_container_width=True): st.rerun()
with col_btn2:
    if st.button('🚀 Relevé manuel', type="primary", use_container_width=True):
        if trigger_github_action() == 204: st.toast("🚀 Requête envoyée !"); time_sleep.sleep(40); st.rerun()

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Disney Live Board", page_icon="🏰", layout="wide")

# --- STYLE CSS TABLEAUX PAR LAND ---
st.markdown("""
<style>
    .land-header {
        background: linear-gradient(90deg, #1e293b 0%, #334155 100%);
        color: #f8fafc;
        padding: 12px 20px;
        border-radius: 12px;
        margin: 25px 0 15px 0;
        font-size: 20px;
        font-weight: 700;
        border-left: 5px solid #4facfe;
    }
    .ride-container {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 15px;
        padding: 12px 18px;
        margin-bottom: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        transition: 0.3s;
    }
    .ride-container:hover {
        background: rgba(255, 255, 255, 0.06);
        transform: translateX(5px);
    }
    .wait-box-magic {
        min-width: 65px;
        height: 50px;
        border-radius: 12px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        color: white;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    }
    .land-title-text { font-size: 16px; font-weight: 600; color: white; margin: 0; }
    .land-sub-text { font-size: 10px; color: #94a3b8; text-transform: uppercase; margin: 0; }
</style>
""", unsafe_allow_html=True)

# --- STRUCTURE DES LANDS ---
lands_structure = {
    "🏰 Disneyland Park": {
        "Main Street": ["Horse-Drawn Streetcars", "Main Street Vehicles", "Disneyland Railroad Main Street Station"],
        "Frontierland": ["Big Thunder Mountain", "Phantom Manor", "Thunder Mesa Riverboat Landing"],
        "Adventureland": ["Pirates of the Caribbean", "Indiana Jones and the Temple of Peril", "La Cabane des Robinson"],
        "Fantasyland": ["Peter Pan's Flight", "It's a small world", "Dumbo the Flying Elephant", "Ratatouille: L'Aventure Totalement Toquée de Rémy", "Mad Hatter's Tea Cups", "Casey Jr. - le Petit Train du Cirque"],
        "Discoveryland": ["Star Wars Hyperspace Mountain", "Star Tours: l'Aventure Continue", "Buzz Lightyear Laser Blast", "Orbitron", "Autopia"]
    },
    "🎬 Walt Disney Studios": {
        "Avengers Campus": ["Avengers Assemble: Flight Force", "Spider-Man W.E.B. Adventure"],
        "Worlds of Pixar": ["Crush's Coaster", "Ratatouille: L'Aventure Totalement Toquée de Rémy", "RC Racer", "Toy Soldiers Parachute Drop"],
        "Production Courtyard": ["The Twilight Zone Tower of Terror"],
        "Adventure Way": ["Raiponce Tangled Spin"]
    }
}

# --- FONCTION DE RENDU CELLULE ---
def render_land_ride(ride_name):
    if df_live.empty: return
    ride_data = df_live[df_live['ride_name'] == ride_name]
    if ride_data.empty: return
    
    row = ride_data.iloc[0]
    info = status_map.get(ride_name, {})
    
    # Calcul des variables (Rehab, Fermé, Panne...)
    is_daw = any(a.lower() in ride_name.lower() for a in RIDES_DAW)
    h_o = EMT_OPENING if ride_name in EMT_EARLY_OPEN else PARK_OPENING
    h_f = DAW_CLOSING if is_daw else DLP_CLOSING
    if ride_name in ANTICIPATED_CLOSINGS: h_f = ANTICIPATED_CLOSINGS[ride_name]
    
    try:
        wait_val = int(row['wait_time'])
    except:
        wait_val = 0
        
    rehab = not info.get('opened_yesterday', True) and not info.get('has_opened_today', False) and not row['is_open']
    
    if rehab: color, label, wait_txt = "#4b5563", "REHAB", "TRVX"
    elif heure_actuelle >= h_f and not row['is_open']: color, label, wait_txt = "#7f1d1d", "FERMÉ", "FIN"
    elif heure_actuelle < h_o and not row['is_open']: color, label, wait_txt = "#1e40af", "SOON", "⌛"
    elif not row['is_open']: color, label, wait_txt = "#92400e", "INCIDENT", "101"
    else:
        if wait_val <= 15: color = "#059669"
        elif wait_val <= 45: color = "#d97706"
        else: color = "#dc2626"
        label, wait_txt = "OUVERT", f"{wait_val}"

    st.markdown(f"""
        <div class="ride-container">
            <div style="display:flex; align-items:center; gap:12px;">
                <span style="font-size:22px;">{get_emoji(ride_name)}</span>
                <div>
                    <p class="land-title-text">{ride_name}</p>
                    <p class="land-sub-text">{label}</p>
                </div>
            </div>
            <div class="wait-box-magic" style="background:{color};">
                <div style="font-size:18px;">{wait_txt}</div>
                <div style="font-size:8px; opacity:0.8;">{"MIN" if wait_txt.isdigit() else ""}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

# --- AFFICHAGE PARC PAR PARC ---
st.title("🏰 Live Board par Land")
st.caption(f"Dernière synchro : {derniere_maj} | Actualisation 60s")

col_dlp, col_daw = st.columns(2)

with col_dlp:
    st.markdown('<div class="land-header">🏰 DISNEYLAND PARK</div>', unsafe_allow_html=True)
    for land, rides in lands_structure["🏰 Disneyland Park"].items():
        with st.expander(f"📍 {land}", expanded=True):
            for r in rides:
                render_land_ride(r)

with col_daw:
    st.markdown('<div class="land-header">🎬 WALT DISNEY STUDIOS</div>', unsafe_allow_html=True)
    for land, rides in lands_structure["🎬 Walt Disney Studios"].items():
        with st.expander(f"📍 {land}", expanded=True):
            for r in rides:
                render_land_ride(r)                        
st.caption("Disney Wait Time Tool | Dashboard v3.1")
