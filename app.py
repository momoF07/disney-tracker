import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime, timedelta
import pytz
import requests
import time
from streamlit_autorefresh import st_autorefresh 
from emojis import get_emoji, get_rides_by_zone

# --- CONFIGURATION ---
st.set_page_config(page_title="Disney Wait Time", page_icon="🏰", layout="centered")

# --- CSS SUR MESURE (LOOK GLASSMORPHISM) ---
st.markdown("""
<style>
    /* 1. Positionnement et Fond de la Popup */
    [data-testid="stPopoverBody"] {
        position: fixed !important;
        top: 50% !important;
        left: 50% !important;
        transform: translate(-50%, -50%) !important;
        width: 90vw !important;
        max-width: 850px !important;
        max-height: 85vh !important;
        background: rgba(15, 18, 25, 0.8) !important;
        backdrop-filter: blur(20px) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 25px !important;
        padding: 25px !important;
        box-shadow: 0 25px 50px rgba(0,0,0,0.8) !important;
        z-index: 999999 !important;
    }

    /* 2. Style des Cartes à l'intérieur */
    .shortcut-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 15px;
        padding: 12px;
        margin-bottom: 10px;
    }
    
    /* 3. Couleurs des Titres Lumineux */
    .title-blue { color: #4facfe; font-weight: bold; font-size: 1.1rem; }
    .title-green { color: #00f2fe; font-weight: bold; font-size: 1.1rem; }
    .title-orange { color: #f9d423; font-weight: bold; font-size: 1.1rem; }
    .title-red { color: #ff0844; font-weight: bold; font-size: 1.1rem; }

    /* 4. Style des codes (les raccourcis) */
    code {
        color: #00ffcc !important;
        background: transparent !important;
        font-size: 1rem !important;
    }
    
    /* Cacher le bouton 'Close' par défaut pour un look plus propre */
    [data-testid="stPopoverBody"] button[kind="secondary"] {
        display: none;
    }
</style>
""", unsafe_allow_html=True)

# --- CONNEXION SUPABASE ---
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
st_autorefresh(interval=60000, key="datarefresh")
paris_tz = pytz.timezone('Europe/Paris')

def trigger_github_action():
    REPO, WORKFLOW_ID, TOKEN = "momoF07/disney-tracker", "check.yml", st.secrets["GITHUB_TOKEN"]
    url = f"https://api.github.com/repos/{REPO}/actions/workflows/{WORKFLOW_ID}/dispatches"
    headers = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        res = requests.post(url, headers=headers, json={"ref": "main"})
        return res.status_code
    except: return 500

# --- INTERFACE PRINCIPALE ---
st.title("🏰 Disney Wait Time")
maintenant = datetime.now(paris_tz)

# Logicet Reset
heure_reset = maintenant.replace(hour=2, minute=0, second=0, microsecond=0)
debut_journee = heure_reset - timedelta(days=1) if maintenant < heure_reset else heure_reset

if st.button('🔄 Actualiser & Forcer un Relevé'):
    with st.spinner("Signal envoyé..."):
        if trigger_github_action() == 204:
            st.toast("🚀 Robot lancé !"); time.sleep(45); st.rerun()

# Récupération données
try:
    response = supabase.table("disney_logs").select("*").gte("created_at", debut_journee.isoformat()).order("created_at", desc=False).execute()
    df_raw = pd.DataFrame(response.data)
except: df_raw = pd.DataFrame()

if not df_raw.empty:
    df_raw['created_at'] = pd.to_datetime(df_raw['created_at']).dt.tz_convert('Europe/Paris')
    df = df_raw[~((df_raw['created_at'].dt.hour >= 2) & (df_raw['created_at'].dt.hour < 8))].copy()
    
    if not df.empty:
        derniere_maj = df['created_at'].max().strftime("%H:%M:%S")
        all_pannes = []
        toutes_attractions = sorted(df['ride_name'].unique())
        
        # --- POPUP D'AIDE ESTHÉTIQUE ---
        st.write("---")
        col_sc, col_help = st.columns([0.88, 0.12])
        
        with col_help:
            with st.popover("❓"):
                st.markdown("<h2 style='text-align:center; color:white; margin-bottom:20px;'>🔍 Raccourcis</h2>", unsafe_allow_html=True)
                
                # --- SECTION 1 : GÉNÉRAL & ANALYSE ---
               st.markdown('<div class="shortcut-card"><p class="title-blue">🎡 Parcs</p></div>', unsafe_allow_html=True)
                col_p1, col_p2, col_p3 = st.columns(3)
                col_p1.code("*ALL")
                col_p2.code("*DLP")
                col_p3.code("*DAW")

                st.markdown("<br>", unsafe_allow_html=True)

                # --- SECTION 2 : DISNEYLAND PARK (Boîtes individuelles toute largeur) ---
                st.markdown('<p class="title-green" style="text-align:center; background: rgba(0,242,254,0.1); border-radius:15px; padding:5px;">🏰 Disneyland Park</p>', unsafe_allow_html=True)
                
                with st.container():
                    st.markdown('<div class="shortcut-card"><small>Main Street</small></div>', unsafe_allow_html=True)
                    col_ms1, col_ms2 = st.columns(2)
                    col_ms1.code("*MS")
                    col_ms2.code("*MAINSTREET")

                    st.markdown('<div class="shortcut-card"><small>Frontierland</small></div>', unsafe_allow_html=True)
                    col_fr1, col_fr2 = st.columns(2)
                    col_fr1.code("*FRONTIER")
                    col_fr2.code("*FRONTIERLAND")

                    st.markdown('<div class="shortcut-card"><small>Adventureland</small></div>', unsafe_allow_html=True)
                    col_ad1, col_ad2 = st.columns(2)
                    col_ad1.code("*ADVENTURE")
                    col_ad2.code("*ADVENTURELAND")

                    st.markdown('<div class="shortcut-card"><small>Fantasyland</small></div>', unsafe_allow_html=True)
                    col_fa1, col_fa2 = st.columns(2)
                    col_fa1.code("*FANTASY")
                    col_fa2.code("*FANTASYLAND")

                    st.markdown('<div class="shortcut-card"><small>Discoveryland</small></div>', unsafe_allow_html=True)
                    col_di1, col_di2 = st.columns(2)
                    col_di1.code("*DISCO")
                    col_di2.code("*DISCOVERYLAND")

                st.markdown("<br>", unsafe_allow_html=True)

                # --- SECTION 3 : ADVENTURE WORLD (Boîtes individuelles toute largeur) ---
                st.markdown('<p class="title-orange" style="text-align:center; background: rgba(249,212,35,0.1); border-radius:15px; padding:5px;">🎬 Disney Adventure World</p>', unsafe_allow_html=True)
                
                with st.container():
                    st.markdown('<div class="shortcut-card"><small>Avengers Campus</small></div>', unsafe_allow_html=True)
                    col_av1, col_av2, col_av3 = st.columns(3)
                    col_av1.code("*CAMPUS")
                    col_av2.code("*AVENGERS")
                    col_av3.code("*AVENGERS-CAMPUS")

                    st.markdown('<div class="shortcut-card"><small>Production Courtyard (Prod3)</small></div>', unsafe_allow_html=True)
                    col_court1, col_court2 = st.columns(2)
                    col_court1.code("*PRODUCTION3")
                    col_court2.code("*PROD3")

                    st.markdown('<div class="shortcut-card"><small>Worlds of Pixar (Prod4)</small></div>', unsafe_allow_html=True)
                    col_pix1, col_pix2, col_pix3, col_pix4 = st.columns(4)
                    col_pix1.code("*PIXAR")
                    col_pix2.code("*WORLD-OF-PIXAR")
                    col_pix3.code("*PRODUCTION4*")
                    col_pix4.code("*PROD4")

                    st.markdown('<div class="shortcut-card"><small>World of Frozen</small></div>', unsafe_allow_html=True)
                    col_fz1, col_fz2, col_fz3 = st.columns(3)
                    col_fz1.code("*WORLD-OF-FROZEN")
                    col_fz2.code("*WOF")
                    col_fz3.code("*FROZEN")

                    st.markdown('<div class="shortcut-card"><small>Adventure Way</small></div>', unsafe_allow_html=True)
                    col_aw1, col_aw2 = st.columns(2)
                    col_aw1.code("*ADVENTURE-WAY")
                    col_aw2.code("*WAY")

        with col_sc:
            sc = st.text_input("Raccourci :", placeholder="ex: *FANTASY, *101...", label_visibility="collapsed")
        
        # Le reste du traitement (sélection, multiselect, affichage) reste identique
        current_selection = st.query_params.get_all("fav")
        if sc == "*101": current_selection = [p['ride'] for p in all_pannes if p['statut'] == "EN_COURS"]
        elif sc == "*102": current_selection = list(set([p['ride'] for p in all_pannes]))
        elif sc.startswith("*"):
            shortcut_selection = get_rides_by_zone(sc, toutes_attractions)
            if shortcut_selection: current_selection = shortcut_selection

        selected_options = st.multiselect("Attractions suivies :", options=toutes_attractions, default=current_selection, format_func=lambda x: f"{get_emoji(x)} {x}")
        st.query_params["fav"] = selected_options
        
        st.caption(f"🕒 Donnée : {derniere_maj} | Auto-refresh : {st.session_state.last_refresh} (60s)")
        
        if selected_options:
            for ride in selected_options:
                ride_df = df[df['ride_name'] == ride].sort_values('created_at', ascending=False)
                if not ride_df.empty:
                    last = ride_df.iloc[0]
                    st.subheader(f"{get_emoji(ride)} {ride}")
                    c1, c2 = st.columns(2)
                    if last['is_open']:
                        c1.success("🟢 OUVERT")
                        c2.metric("Attente", f"{int(last['wait_time'])} min")
                    else:
                        c1.error("🔴 FERMÉ / PANNE")
                        c2.metric("Attente", "- - -")
                    st.divider()
    else:
        st.warning("😴 Maintenance nocturne.")
else:
    st.warning("📭 Aucune donnée.")
