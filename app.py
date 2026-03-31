import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime, timedelta, time as dt_time
import pytz
import requests
import time
from streamlit_autorefresh import st_autorefresh 
from emojis import get_emoji, get_rides_by_zone

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Disney Wait Time", page_icon="🏰", layout="centered")

# --- STYLE CSS : POPUP CENTRALE & ESTHÉTIQUE ---
st.markdown("""
<style>
    [data-testid="stPopoverBody"] {
        position: fixed !important;
        top: 50% !important;
        left: 50% !important;
        transform: translate(-50%, -50%) !important;
        width: 85vw !important;
        max-width: 650px !important;
        max-height: 80vh !important;
        overflow-y: auto !important;
        background-color: rgba(17, 20, 28, 0.9) !important;
        backdrop-filter: blur(15px) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 20px !important;
        padding: 20px !important;
        z-index: 999999 !important;
    }
    .shortcut-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        padding: 8px;
        margin-top: 10px;
        margin-bottom: 5px;
    }
    .title-blue { color: #4facfe; font-weight: bold; }
    .title-green { color: #00f2fe; font-weight: bold; }
    .title-orange { color: #f9d423; font-weight: bold; }
    .title-red { color: #ff0844; font-weight: bold; }
    [data-testid='stMetricValue'] { font-size: 1.8rem; }
    .stButton button { width: 100%; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# --- INITIALISATION ÉTAT DE SESSION ---
paris_tz = pytz.timezone('Europe/Paris')
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = datetime.now(paris_tz).strftime("%H:%M:%S")

# --- CONNEXION SUPABASE ---
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

# --- ACTUALISATION AUTOMATIQUE ---
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

# --- INTERFACE ---
st.title("🏰 Disney Wait Time")
maintenant = datetime.now(paris_tz)

# Logique de Reset (2h du matin Paris)
heure_reset = maintenant.replace(hour=2, minute=0, second=0, microsecond=0)
debut_journee = heure_reset - timedelta(days=1) if maintenant < heure_reset else heure_reset

if st.button('🔄 Actualiser & Forcer un Relevé'):
    with st.spinner("Signal envoyé..."):
        if trigger_github_action() == 204:
            st.toast("🚀 Robot lancé !"); time.sleep(45); st.rerun()

# --- RÉCUPÉRATION DES DONNÉES SÉCURISÉE (Correction du bug de 15h30) ---
try:
    # On convertit le début de journée Paris en UTC pour la requête Supabase
    debut_utc = debut_journee.astimezone(pytz.utc)
    
    response = supabase.table("disney_logs")\
        .select("*")\
        .gte("created_at", debut_utc.isoformat())\
        .order("created_at", desc=False)\
        .execute()
    df_raw = pd.DataFrame(response.data)
except Exception as e:
    st.error(f"Erreur Supabase : {e}")
    df_raw = pd.DataFrame()

if not df_raw.empty:
    # On s'assure que Pandas traite bien les dates comme de l'UTC avant de convertir
    df_raw['created_at'] = pd.to_datetime(df_raw['created_at'])
    if df_raw['created_at'].dt.tz is None:
        df_raw['created_at'] = df_raw['created_at'].dt.tz_localize('UTC')
    
    # Conversion finale en heure de Paris
    df_raw['created_at'] = df_raw['created_at'].dt.tz_convert('Europe/Paris')
    
    # Filtrage final : Uniquement depuis le reset de 2h du matin ET hors maintenance
    df = df_raw[df_raw['created_at'] >= debut_journee].copy()
    df = df[~((df['created_at'].dt.hour >= 2) & (df['created_at'].dt.hour < 8))].copy()
    
    if not df.empty:
        derniere_maj = df['created_at'].max().strftime("%H:%M:%S")
        all_pannes = []
        toutes_attractions = sorted(df['ride_name'].unique())
        
        # --- CALCUL COMPLET DES PANNES ---
        for ride_name in toutes_attractions:
            ride_data = df[df['ride_name'] == ride_name].sort_values('created_at')
            en_panne, debut_panne = False, None
            for i, row in ride_data.iterrows():
                if not row['is_open'] and not en_panne:
                    en_panne, debut_panne = True, row['created_at']
                elif row['is_open'] and en_panne:
                    all_pannes.append({
                        "ride": ride_name, "debut": debut_panne, "fin": row['created_at'], 
                        "duree": int((row['created_at'] - debut_panne).total_seconds() / 60), 
                        "statut": "TERMINEE"
                    })
                    en_panne = False
            if en_panne:
                all_pannes.append({"ride": ride_name, "debut": debut_panne, "fin": None, "statut": "EN_COURS"})

        # --- LOGIQUE RACCOURCIS (POPUP) ---
        st.write("---")
        col_sc, col_help = st.columns([0.88, 0.12])
        
                with col_help:
            with st.popover("❓"):
                st.markdown("<h2 style='text-align:center; color:white; margin-bottom:20px;'>🔍 Raccourcis</h2>", unsafe_allow_html=True)
                
                # --- SECTION 1 : GÉNÉRAL (Sans colonnes c1/c2 car Analyse est supprimé) ---
                st.markdown('<div class="shortcut-card"><p class="title-blue">🎡 Parcs</p></div>', unsafe_allow_html=True)
                col_p1, col_p2, col_p3 = st.columns(3)
                col_p1.code("*ALL")
                col_p2.code("*DLP")
                col_p3.code("*DAW")

                st.markdown("<br>", unsafe_allow_html=True)

                # --- SECTION 2 : DISNEYLAND PARK ---
                st.markdown('<p class="title-green" style="text-align:center; background: rgba(0,242,254,0.1); border-radius:10px; padding:5px;">🏰 Disneyland Park</p>', unsafe_allow_html=True)
                
                # Main Street
                st.markdown('<div class="shortcut-card"><small>Main Street</small></div>', unsafe_allow_html=True)
                col_ms1, col_ms2 = st.columns(2)
                col_ms1.code("*MS")
                col_ms2.code("*MAINSTREET")

                # Frontierland
                st.markdown('<div class="shortcut-card"><small>Frontierland</small></div>', unsafe_allow_html=True)
                col_fr1, col_fr2 = st.columns(2)
                col_fr1.code("*FRONTIER")
                col_fr2.code("*FRONTIERLAND")

                # Adventureland
                st.markdown('<div class="shortcut-card"><small>Adventureland</small></div>', unsafe_allow_html=True)
                col_ad1, col_ad2 = st.columns(2)
                col_ad1.code("*ADVENTURE")
                col_ad2.code("*ADVENTURELAND")

                # Fantasyland
                st.markdown('<div class="shortcut-card"><small>Fantasyland</small></div>', unsafe_allow_html=True)
                col_fa1, col_fa2 = st.columns(2)
                col_fa1.code("*FANTASY")
                col_fa2.code("*FANTASYLAND")

                # Discoveryland
                st.markdown('<div class="shortcut-card"><small>Discoveryland</small></div>', unsafe_allow_html=True)
                col_di1, col_di2 = st.columns(2)
                col_di1.code("*DISCO")
                col_di2.code("*DISCOVERYLAND")

                st.markdown("<br>", unsafe_allow_html=True)

                # --- SECTION 3 : ADVENTURE WORLD ---
                st.markdown('<p class="title-orange" style="text-align:center; background: rgba(249,212,35,0.1); border-radius:10px; padding:5px;">🎬 Adventure World</p>', unsafe_allow_html=True)
                
                # Avengers
                st.markdown('<div class="shortcut-card"><small>Avengers Campus</small></div>', unsafe_allow_html=True)
                col_av1, col_av2, col_av3 = st.columns(3)
                col_av1.code("*CAMPUS")
                col_av2.code("*AVENGERS")
                col_av3.code("*AVENGERS-CAMPUS")

                # Pixar
                st.markdown('<div class="shortcut-card"><small>Worlds of Pixar</small></div>', unsafe_allow_html=True)
                col_pix1, col_pix2 = st.columns(2)
                col_pix1.code("*PIXAR")
                col_pix2.code("*PROD4")

                # Production 3
                st.markdown('<div class="shortcut-card"><small>Production 3</small></div>', unsafe_allow_html=True)
                st.code("*PROD3")

                # Frozen
                st.markdown('<div class="shortcut-card"><small>World of Frozen</small></div>', unsafe_allow_html=True)
                col_fz1, col_fz2 = st.columns(2)
                col_fz1.code("*WOF")
                col_fz2.code("*FROZEN")

                # Adventure Way
                st.markdown('<div class="shortcut-card"><small>Adventure Way</small></div>', unsafe_allow_html=True)
                st.code("*WAY")

        with col_sc:
            sc = st.text_input("Raccourci :", placeholder="ex: *FANTASY...", label_visibility="collapsed")
        
        current_selection = st.query_params.get_all("fav")
        if sc.startswith("*"):
            shortcut_selection = get_rides_by_zone(sc, toutes_attractions)
            if shortcut_selection: current_selection = shortcut_selection

        selected_options = st.multiselect("Attractions suivies :", options=toutes_attractions, default=current_selection, format_func=lambda x: f"{get_emoji(x)} {x}")
        st.query_params["fav"] = selected_options
        
        st.caption(f"🕒 Donnée : {derniere_maj} | Auto-refresh : {st.session_state.last_refresh} (60s)")
        
        # --- AFFICHAGE DES ATTRACTIONS ---
        if selected_options:
            st.divider()
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
                    
                    # Historique et pannes actuelles
                    ride_pannes = [p for p in all_pannes if p['ride'] == ride]
                    panne_actuelle = next((p for p in ride_pannes if p['statut'] == "EN_COURS"), None)
                    if panne_actuelle:
                        diff = int((maintenant - panne_actuelle['debut']).total_seconds() / 60)
                        st.warning(f"⚠️ En panne depuis {diff} min (à {panne_actuelle['debut'].strftime('%H:%M')})")
                    
                    with st.expander("📜 Historique des pannes du jour"):
                        if ride_pannes:
                            for p in reversed(ride_pannes):
                                if p['statut'] == "TERMINEE":
                                    st.write(f"• De {p['debut'].strftime('%H:%M')} à {p['fin'].strftime('%H:%M')} ({p['duree']} min)")
                                else:
                                    st.write(f"• ⚠️ En cours depuis {p['debut'].strftime('%H:%M')}")
                        else:
                            st.write("✅ Pas de panne détectée")
                    st.divider()

        # --- FLUX DES PANNES GLOBAL ---
        st.subheader("🚨 Flux des dernières pannes")
        flux = sorted(all_pannes, key=lambda x: x['debut'], reverse=True)[:5]
        if flux:
            for p in flux:
                if p['statut'] == "EN_COURS": st.error(f"🔴 {p['ride']} ({p['debut'].strftime('%H:%M')})")
                else: st.info(f"✅ {p['ride']} rouvert à {p['fin'].strftime('%H:%M')} ({p['duree']} min)")
        else:
            st.write("✅ Aucune panne enregistrée.")
    else:
        st.warning("😴 Maintenance nocturne (02h-08h).")
else:
    st.warning("📭 Aucune donnée disponible aujourd'hui.")

st.markdown("<style>[data-testid='stMetricValue'] { font-size: 1.8rem; } .stButton button { width: 100%; border-radius: 10px; }</style>", unsafe_allow_html=True)
