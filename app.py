import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime, timedelta
import pytz
import requests
import time
from streamlit_autorefresh import st_autorefresh 
from emojis import get_emoji, get_rides_by_zone

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Disney Live Tracker", page_icon="🏰", layout="centered")

# --- DESIGN SYSTEM (CSS AVANCÉ) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;800&display=swap');

    /* Global Style */
    html, body, [class*="st-"] {
        font-family: 'Poppins', sans-serif;
    }

    .main {
        background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
    }

    /* Popover Styling */
    [data-testid="stPopoverBody"] {
        background: rgba(15, 23, 42, 0.95) !important;
        backdrop-filter: blur(20px) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 25px !important;
        padding: 30px !important;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5) !important;
    }

    /* Shortcut Cards */
    .shortcut-card {
        background: rgba(255, 255, 255, 0.03);
        border-radius: 15px;
        padding: 12px;
        margin-bottom: 10px;
        border-left: 4px solid #4facfe;
        transition: all 0.3s ease;
    }
    .shortcut-card:hover {
        background: rgba(255, 255, 255, 0.07);
        transform: translateX(5px);
    }

    /* Section Headers */
    .title-blue { color: #38bdf8; font-weight: 800; font-size: 1.1rem; border-bottom: 2px solid #38bdf8; padding-bottom: 5px; }
    .title-green { color: #4ade80; font-weight: 800; font-size: 1.1rem; border-bottom: 2px solid #4ade80; padding-bottom: 5px; }
    .title-orange { color: #fbbf24; font-weight: 800; font-size: 1.1rem; border-bottom: 2px solid #fbbf24; padding-bottom: 5px; }

    /* Metrics & Status */
    [data-testid="stMetricValue"] {
        font-weight: 800 !important;
        background: linear-gradient(to right, #4facfe 0%, #00f2fe 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .stButton button {
        background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%) !important;
        color: white !important;
        border: none !important;
        font-weight: 600 !important;
        border-radius: 12px !important;
        height: 3rem !important;
        transition: all 0.3s ease !important;
    }
    .stButton button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 10px 20px rgba(79, 172, 254, 0.3) !important;
    }

    /* Code Snippets */
    code {
        color: #f8fafc !important;
        background: rgba(56, 189, 248, 0.2) !important;
        padding: 2px 6px !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- LOGIQUE INITIALISATION ---
paris_tz = pytz.timezone('Europe/Paris')
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = datetime.now(paris_tz).strftime("%H:%M:%S")

supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
st_autorefresh(interval=60000, key="datarefresh")
st.session_state.last_refresh = datetime.now(paris_tz).strftime("%H:%M:%S")

def trigger_github_action():
    REPO, WORKFLOW_ID, TOKEN = "momoF07/disney-tracker", "check.yml", st.secrets["GITHUB_TOKEN"]
    url = f"https://api.github.com/repos/{REPO}/actions/workflows/{WORKFLOW_ID}/dispatches"
    headers = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        res = requests.post(url, headers=headers, json={"ref": "main"})
        return res.status_code
    except: return 500

# --- HEADER ---
st.markdown("<h1 style='text-align: center; font-size: 3rem;'>🏰 Disney Tracker</h1>", unsafe_allow_html=True)
maintenant = datetime.now(paris_tz)

col_info, col_btn = st.columns([0.7, 0.3])
with col_info:
    st.markdown(f"🗓️ **{maintenant.strftime('%d %B %Y')}**<br>🕒 Dernière synchro : `{st.session_state.last_refresh}`", unsafe_allow_html=True)
with col_btn:
    if st.button('🔄 Refresh'):
        with st.spinner("🚀"):
            if trigger_github_action() == 204:
                st.toast("Robot envoyé !"); time.sleep(45); st.rerun()

# --- RÉCUPÉRATION DATA ---
heure_reset = maintenant.replace(hour=2, minute=0, second=0, microsecond=0)
debut_journee = heure_reset - timedelta(days=1) if maintenant < heure_reset else heure_reset

try:
    response = supabase.table("disney_logs").select("*").order("created_at", desc=True).limit(3000).execute()
    df = pd.DataFrame(response.data)
    if not df.empty:
        df['created_at'] = pd.to_datetime(df['created_at']).dt.tz_localize('UTC').dt.tz_convert('Europe/Paris')
        df = df[df['created_at'] >= debut_journee]
except:
    df = pd.DataFrame()

# --- SECTION FILTRES & POPOVER ---
st.write("")
col_search, col_pop = st.columns([0.85, 0.15])

with col_pop:
    with st.popover("❓"):
        st.markdown("<h2 style='text-align:center; color:white; margin-bottom:20px;'>🔍 Aide & Raccourcis</h2>", unsafe_allow_html=True)
        
        # Parcs
        st.markdown('<p class="title-blue">🎡 Parcs & Systèmes</p>', unsafe_allow_html=True)
        cp1, cp2, cp3 = st.columns(3)
        cp1.code("*ALL"); cp2.code("*DLP"); cp3.code("*DAW")
        
        st.markdown('<div class="shortcut-card"><small>Debug & Tests</small></div>', unsafe_allow_html=True)
        ct1, ct2, ct3 = st.columns(3)
        ct1.code("*101"); ct2.code("*102"); ct3.code("*TEST")

        # Disneyland Park
        st.markdown('<p class="title-green" style="margin-top:20px;">🏰 Disneyland Park</p>', unsafe_allow_html=True)
        lands_dlp = {
            "Main Street": ["*MS", "*MAINSTREET"],
            "Frontierland": ["*FRONTIER", "*FRONTIERLAND"],
            "Adventureland": ["*ADVENTURE", "*ADVENTURELAND"],
            "Fantasyland": ["*FANTASY", "*FANTASYLAND"],
            "Discoveryland": ["*DISCO", "*DISCOVERYLAND"]
        }
        for land, codes in lands_dlp.items():
            st.markdown(f'<div class="shortcut-card" style="border-left-color:#4ade80;"><small>{land}</small></div>', unsafe_allow_html=True)
            cl1, cl2 = st.columns(2)
            cl1.code(codes[0]); cl2.code(codes[1])

        # Adventure World
        st.markdown('<p class="title-orange" style="margin-top:20px;">🎬 Adventure World</p>', unsafe_allow_html=True)
        
        st.markdown('<div class="shortcut-card" style="border-left-color:#fbbf24;"><small>Avengers Campus</small></div>', unsafe_allow_html=True)
        ca1, ca2, ca3 = st.columns(3)
        ca1.code("*CAMPUS"); ca2.code("*AVENGERS"); ca3.code("*AVENGERS-CAMPUS")

        st.markdown('<div class="shortcut-card" style="border-left-color:#fbbf24;"><small>Worlds of Pixar</small></div>', unsafe_allow_html=True)
        cpx1, cpx2, cpx3 = st.columns(3)
        cpx1.code("*PIXAR"); cpx2.code("*PROD4"); cpx3.code("*PRODUCTION4")

        st.markdown('<div class="shortcut-card" style="border-left-color:#fbbf24;"><small>Frozen & Zones</small></div>', unsafe_allow_html=True)
        cf1, cf2, cf3 = st.columns(3)
        cf1.code("*WOF"); cf2.code("*WAY"); cf3.code("*PROD3")

        st.markdown('<div class="shortcut-card" style="border-left-color:#fbbf24;"><small>Alias Longs</small></div>', unsafe_allow_html=True)
        st.code("*WORLD-OF-FROZEN")
        st.code("*ADVENTURE-WAY")

with col_search:
    sc = st.text_input("Rechercher une zone (ex: *FANTASY)", label_visibility="collapsed")

# --- MULTISELECT & DISPLAY ---
if not df.empty:
    toutes = sorted(df['ride_name'].unique())
    current = st.query_params.get_all("fav")
    if sc.startswith("*"):
        shortcut = get_rides_by_zone(sc, toutes)
        if shortcut: current = shortcut

    selected = st.multiselect("Sélectionnez vos attractions :", options=toutes, default=[i for i in current if i in toutes], format_func=lambda x: f"{get_emoji(x)} {x}")
    st.query_params["fav"] = selected

    if selected:
        st.write("")
        for ride in selected:
            ride_df = df[df['ride_name'] == ride].iloc[0]
            with st.container():
                st.markdown(f"""
                <div style="background: rgba(255,255,255,0.05); padding: 20px; border-radius: 20px; margin-bottom: 20px; border: 1px solid rgba(255,255,255,0.1);">
                    <h3 style="margin:0;">{get_emoji(ride)} {ride}</h3>
                </div>
                """, unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                if ride_df['is_open']:
                    c1.success("🟢 OUVERT")
                    c2.metric("Attente", f"{int(ride_df['wait_time'])} min")
                else:
                    c1.error("🔴 FERMÉ")
                    c2.metric("Attente", "--")
                st.write("---")
else:
    st.info("😴 En attente de données...")
