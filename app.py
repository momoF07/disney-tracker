import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime, timedelta, time as dt_time
import pytz
import requests
import time
from streamlit_autorefresh import st_autorefresh 
from emojis import get_emoji, get_rides_by_zone
from config import PARK_OPENING, PARK_CLOSING

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Disney Wait Time", page_icon="🏰", layout="centered")

# --- STYLE CSS ---
st.markdown("""
<style>
    [data-testid="stPopoverBody"] {
        position: fixed !important;
        top: 50% !important;
        left: 50% !important;
        transform: translate(-50%, -50%) !important;
        width: 90vw !important;
        max-width: 800px !important;
        max-height: 80vh !important;
        overflow-y: auto !important;
        background-color: rgba(28, 31, 46, 0.98) !important;
        backdrop-filter: blur(20px) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 24px !important;
        padding: 25px !important;
        z-index: 999999 !important;
        box-shadow: 0 20px 40px rgba(0,0,0,0.5) !important;
    }
    .blue-t { color: #4facfe; }
    .green-t { color: #00f2fe; }
    .orange-t { color: #f9d423; }
    
    code {
        color: #ff9a9e !important;
        background: rgba(255,154,158,0.1) !important;
    }
    [data-testid='stMetricValue'] { font-size: 1.8rem; }
    .stButton button { width: 100%; border-radius: 12px; }
</style>
""", unsafe_allow_html=True)

# --- INITIALISATION ---
paris_tz = pytz.timezone('Europe/Paris')

# Correction Bug Refresh : On initialise last_refresh s'il n'existe pas
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = datetime.now(paris_tz).strftime("%H:%M:%S")

# On récupère le compteur de l'auto-refresh
refresh_count = st_autorefresh(interval=60000, key="datarefresh")

# Si le compteur a augmenté, on met à jour l'heure de dernier refresh en session
if refresh_count > 0:
    st.session_state.last_refresh = datetime.now(paris_tz).strftime("%H:%M:%S")

supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

# --- AJOUT : FONCTION POUR GÉRER MINUIT ---
def is_park_theoretically_open(current, opening, closing):
    if opening <= closing:
        return opening <= current <= closing
    return current >= opening or current <= closing

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
heure_actuelle = maintenant.time()

@st.dialog("⚠️ Système en pause")
def popup_alerte_donnees():
    st.write("Aucune donnée n'a été enregistrée pour le moment aujourd'hui.")
    st.info("Le robot Disney est peut-être en attente de l'ouverture ou en maintenance.")
    if st.button("Tenter de forcer un relevé maintenant"):
        if trigger_github_action() == 204:
            st.toast("🚀 Signal envoyé au robot ! Merci de patienter un instant.")
            time.sleep(45)
            st.rerun()

# AJOUT : Changement de l'heure de reset à 2h30 pour s'aligner sur le worker
heure_reset = maintenant.replace(hour=2, minute=30, second=0, microsecond=0)
debut_journee = heure_reset if maintenant >= heure_reset else heure_reset - timedelta(days=1)

# --- SECTION BOUTONS (MANUEL + ROBOT) ---
col_btn1, col_btn2 = st.columns(2)

with col_btn1:
    if st.button('🔄 Rafraîchir l\'Affichage'):
        st.rerun()

with col_btn2:
    if st.button('🚀 Forcer un Relevé Robot'):
        with st.spinner("Signal envoyé..."):
            if trigger_github_action() == 204:
                st.toast("🚀 Robot lancé !"); time.sleep(45); st.rerun()

# --- RÉCUPÉRATION DES DONNÉES ---
try:
    # On récupère le Live (Temps d'attente récents)
    resp_live = supabase.table("disney_logs").select("*").order("created_at", desc=True).limit(200).execute()
    df_raw = pd.DataFrame(resp_live.data)
    
    # On récupère les pannes depuis la nouvelle table dédiée
    resp_101 = supabase.table("logs_101").select("*").gte("start_time", debut_journee.isoformat()).execute()
    df_pannes = pd.DataFrame(resp_101.data)
except Exception as e:
    st.error(f"Erreur Supabase : {e}")
    df_raw, df_pannes = pd.DataFrame(), pd.DataFrame()


if not df_raw.empty:
    # --- GESTION TIMEZONE ROBUSTE ---
    df_raw['created_at'] = pd.to_datetime(df_raw['created_at'])
    if df_raw['created_at'].dt.tz is None:
        df_raw['created_at'] = df_raw['created_at'].dt.tz_localize('UTC')
    df_raw['created_at'] = df_raw['created_at'].dt.tz_convert('Europe/Paris')
    
    df = df_raw[df_raw['created_at'] >= debut_journee].copy()
    
    # Si le filtre vide tout, on garde quand même les dernières données pour l'affichage de fermeture
    if df.empty and not df_raw.empty:
        df = df_raw.head(300).copy()

    if not df.empty:
        derniere_maj = df['created_at'].max().strftime("%H:%M:%S")
        all_pannes = []
        toutes_attractions = sorted(df['ride_name'].unique())
        
        # --- LOGIQUE PARC FERMÉ (DÉTECTION GLOBALE) ---
        derniere_maj_time = df['created_at'].max()
        etat_actuel = df[df['created_at'] == derniere_maj_time]
        tous_fermes_globalement = not etat_actuel['is_open'].any()
        
        # --- PRÉPARATION DES PANNES (LUES DEPUIS LOGS_101) ---
        all_pannes = []
        if not df_pannes.empty:
            for _, row in df_pannes.iterrows():
                # On convertit les dates pour l'affichage
                d = pd.to_datetime(row['start_time']).astimezone(paris_tz)
                f = pd.to_datetime(row['end_time']).astimezone(paris_tz) if pd.notna(row['end_time']) else None
                
                all_pannes.append({
                    "ride": row['ride_name'],
                    "debut": d,
                    "fin": f,
                    "duree": int((f - d).total_seconds() / 60) if f else 0,
                    "statut": "EN_COURS" if f is None else "TERMINEE"
                })

        # --- FILTRES ---
        st.write("---")
        col_sc, col_help = st.columns([0.85, 0.15])
        with col_help:
            with st.popover("❓"):
                st.markdown("""
                <style>
                    .main-title {
                        text-align: center; 
                        background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%);
                        -webkit-background-clip: text;
                        -webkit-text-fill-color: transparent;
                        font-weight: 800;
                        font-size: 28px;
                        margin-bottom: 25px;
                    }
                    .cat-badge {
                        padding: 5px 15px;
                        border-radius: 12px;
                        font-size: 18px;
                        font-weight: 600;
                        letter-spacing: 1px;
                        display: block;
                        text-align: center;
                        margin: 20px 0 10px 0;
                    }
                    .bg-blue { background: rgba(79, 172, 254, 0.15); color: #4facfe; border: 1px solid rgba(79, 172, 254, 0.3); }
                    .bg-green { background: rgba(74, 222, 128, 0.15); color: #4ade80; border: 1px solid rgba(74, 222, 128, 0.3); }
                    .bg-orange { background: rgba(251, 191, 36, 0.15); color: #fbbf24; border: 1px solid rgba(251, 191, 36, 0.3); }
                    .shortcut-box {
                        background: rgba(255, 255, 255, 0.03);
                        border: 1px solid rgba(255, 255, 255, 0.05);
                        border-radius: 12px;
                        padding: 10px;
                        margin-bottom: 8px;
                    }
                    .shortcut-label {
                        font-size: 15px;
                        color: #94a3b8;
                        text-transform: uppercase;
                        margin-bottom: 5px;
                        display: block;
                    }
                </style>
                """, unsafe_allow_html=True)

                st.markdown('<p class="main-title">🔍 INDEX DES CODES</p>', unsafe_allow_html=True)

                st.markdown('<span class="cat-badge bg-blue">🎡 PARCS</span>', unsafe_allow_html=True)
                with st.container():
                    c1, c2, c3 = st.columns(3)
                    c1.code("*ALL"); c2.code("*DLP"); c3.code("*DAW")

                st.markdown('<span class="cat-badge bg-green">🏰 DISNEYLAND PARK</span>', unsafe_allow_html=True)
                lands_dlp_map = {
                    "Main Street": ["*MS", "*MAINSTREET"],
                    "Frontierland": ["*FRONTIER", "*FRONTIERLAND"],
                    "Adventureland": ["*ADVENTURE", "*ADVENTURELAND"],
                    "Fantasyland": ["*FANTASY", "*FANTASYLAND"],
                    "Discoveryland": ["*DISCO", "*DISCOVERYLAND"]
                }
                for land, codes in lands_dlp_map.items():
                    st.markdown(f'<div class="shortcut-box"><span class="shortcut-label">{land}</span>', unsafe_allow_html=True)
                    cl1, cl2 = st.columns(2)
                    cl1.code(codes[0]); cl2.code(codes[1])
                    st.markdown('</div>', unsafe_allow_html=True)

                st.markdown('<span class="cat-badge bg-orange">🎬 ADVENTURE WORLD</span>', unsafe_allow_html=True)
                st.markdown('<div class="shortcut-box"><span class="shortcut-label">Avengers Campus</span>', unsafe_allow_html=True)
                ca1, ca2, ca3 = st.columns(3)
                ca1.code("*CAMPUS"); ca2.code("*AVENGERS"); ca3.code("*AVENGERS-CAMPUS")
                st.markdown('</div>', unsafe_allow_html=True)

                st.markdown('<div class="shortcut-box"><span class="shortcut-label">Production Courtyard / Production 3</span>', unsafe_allow_html=True)
                pc1, pc2, pc3 = st.columns(3)
                pc1.code("*COURTYARD"); pc2.code("*PRODUCTION3"); pc3.code("*PROD3")
                st.markdown('</div>', unsafe_allow_html=True)

                st.markdown('<div class="shortcut-box"><span class="shortcut-label">Worlds of Pixar / Production 4</span>', unsafe_allow_html=True)
                cpx1, cpx2, cpx3, cpx4 = st.columns(4)
                cpx1.code("*PIXAR"); cpx2.code("*WORLD-OF-PIXAR"); cpx3.code("*PROD4"); cpx4.code("*PRODUCTION4")
                st.markdown('</div>', unsafe_allow_html=True)

                st.markdown('<div class="shortcut-box"><span class="shortcut-label">World of Frozen</span>', unsafe_allow_html=True)
                cfz1, cfz2, cfz3 = st.columns(3)
                cfz1.code("*WOF"); cfz2.code("*FROZEN"); cfz3.code("*WORLD-OF-FROZEN")
                st.markdown('</div>', unsafe_allow_html=True)

                st.markdown('<div class="shortcut-box"><span class="shortcut-label">Adventure Way</span>', unsafe_allow_html=True)
                aw1, aw2 = st.columns(2)
                aw1.code("*WAY"); aw2.code("*ADVENTURE-WAY")
                st.markdown('</div>', unsafe_allow_html=True)

                st.caption("✨ Astuce : Tapez le code et appuyez sur Entrée.")
        with col_sc:
            sc = st.text_input("Raccourci...", placeholder="ex: *FANTASY / *FRONTIER / *CAMPUS / *DLP / etc...", label_visibility="collapsed")
        
        current_selection = st.query_params.get_all("fav")
        if sc.startswith("*"):
            shortcut_selection = get_rides_by_zone(sc, toutes_attractions, all_pannes)
            if shortcut_selection: current_selection = shortcut_selection

        valid_default = [item for item in current_selection if item in toutes_attractions]
        selected_options = st.multiselect("Attractions suivies :", options=toutes_attractions, default=valid_default, format_func=lambda x: f"{get_emoji(x)} {x}")
        st.query_params["fav"] = selected_options
        
        # --- LIGNE DE L'HEURE ---
        st.caption(f"🕒 Donnée : {derniere_maj} | Auto-Refresh : {st.session_state.last_refresh}")

        # --- AJOUT : LOGIQUE D'AFFICHAGE DU MESSAGE DE FERMETURE DYNAMIQUE ---
        parc_theoriquement_ouvert = is_park_theoretically_open(heure_actuelle, PARK_OPENING, PARK_CLOSING)
        
        if not parc_theoriquement_ouvert or tous_fermes_globalement:
            st.info(f"ℹ️ Le parc est actuellement fermé. Les horaires actuellement configurées sont {PARK_OPENING} -> {PARK_CLOSING}\nLes dernières données ont été envoyées à {derniere_maj}.")
            parc_actuellement_ferme = True
        else:
            parc_actuellement_ferme = False
        
        # --- AFFICHAGE DES ATTRACTIONS ---
        if selected_options:
            st.divider()
            for ride in selected_options:
                ride_df = df[df['ride_name'] == ride].sort_values('created_at', ascending=False)
                if not ride_df.empty:
                    last = ride_df.iloc[0]
                    a_deja_ouvert_ce_ride = ride_df['is_open'].any()
                    
                    # On cherche si une panne est déclarée "EN_COURS" dans logs_101
                    panne_actuelle = next((p for p in all_pannes if p['ride'] == ride and p['statut'] == "EN_COURS"), None)
                    
                    st.subheader(f"{get_emoji(ride)} {ride}")
                    c1, c2 = st.columns(2)
                    
                    # 1. PRIORITÉ ABSOLUE : LE PARC EST FERMÉ (NUIT)
                    if parc_actuellement_ferme:
                        c1.error("🔴 PARC FERMÉ")
                        c2.metric("Attente", "- - -")
                    
                    # 2. PRIORITÉ SECONDAIRE : L'ATTRACTION EST EN PANNE (101)
                    # Si une panne est ouverte dans logs_101, on affiche INTERRUPTION même si elle n'a pas encore ouvert officiellement
                    elif panne_actuelle or not last['is_open']:
                        c1.warning("🔴 INTERRUPTION / 101")
                        if panne_actuelle:
                            min_inc = int((maintenant - panne_actuelle['debut']).total_seconds() / 60)
                            st.caption(f"⚠️ En panne depuis **{max(0, min_inc)} min**")
                        c2.metric("Attente", "- - -")

                    # 3. CAS CLASSIQUE : EN ATTENTE D'OUVERTURE (PAS DE 101)
                    elif (heure_actuelle < PARK_OPENING) or (not a_deja_ouvert_ce_ride):
                        c1.info("🕒 FERMÉ")
                        c2.metric("Attente", "- - -")
                        st.caption("⏳ En attente de l'ouverture.")
                    
                    # 4. L'ATTRACTION EST OUVERTE
                    else:
                        c1.success("🟢 OUVERT")
                        c2.metric("Attente", f"{int(last['wait_time'])} min")
                    
                    with st.expander("📜 Historique des pannes"):
                        hist_pannes = [p for p in all_pannes if p['ride'] == ride and p['statut'] == "TERMINEE"]
                        if hist_pannes:
                            for p in sorted(hist_pannes, key=lambda x: x['debut'], reverse=True):
                                st.write(f"• De {p['debut'].strftime('%H:%M')} à {p['fin'].strftime('%H:%M')} ({p['duree']} min)")
                        else: st.write("✅ Aucune panne terminée aujourd'hui.")
                    st.divider()

               # --- FLUX DES DERNIÈRES PANNES ---
        st.subheader("🚨 Dernières interruptions")
        
        # On ne garde que les pannes qui ont réellement commencé APRES le reset de 2h30
        # et on s'assure que la table n'est pas vide
        if not df_pannes.empty:
            # Conversion de la colonne start_time en datetime pour le filtre
            df_pannes['start_time_dt'] = pd.to_datetime(df_pannes['start_time'])
            
            # FILTRE CRUCIAL : On ignore les pannes fantômes créées juste après un clear de DB
            flux_clean = df_pannes[df_pannes['start_time_dt'] >= debut_journee].sort_values('start_time', ascending=False).head(5)
            
            if not flux_clean.empty:
                for _, p in flux_clean.iterrows():
                    d = pd.to_datetime(p['start_time']).astimezone(paris_tz)
                    if pd.isna(p['end_time']):
                        st.error(f"🔴 {p['ride_name']} >> depuis {d.strftime('%H:%M')}")
                    else:
                        f = pd.to_datetime(p['end_time']).astimezone(paris_tz)
                        dur = int((f - d).total_seconds() / 60)
                        st.success(f"✅ {p['ride_name']} >> fini à {f.strftime('%H:%M')} ({dur} min)")
            else:
                st.write("✅ Aucune interruption réelle détectée.")
        else:
            st.write("✅ Aucune interruption détectée.")

    else: st.warning("⏳ En attente des premières données de la journée.")
else: st.warning(f"📭 Aucune donnée disponible.\nMerci de patienter jusqu'à {PARK_OPENING}.")
    # --- À LA TOUTE FIN DU CODE ---
if df_raw.empty:
    # On vérifie si on a déjà montré la popup pour ne pas boucler à l'infini
    if "popup_shown" not in st.session_state:
        st.session_state.popup_shown = True
        popup_alerte_donnees()
else:
    # Si des données reviennent, on réinitialise pour la prochaine fois
    if "popup_shown" in st.session_state:
        del st.session_state.popup_shown

st.divider()
st.caption("Disney Wait Time Tool")
