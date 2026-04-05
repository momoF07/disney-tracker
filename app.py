import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime, timedelta
import pytz
import requests
import time
from streamlit_autorefresh import st_autorefresh 
from emojis import get_emoji, get_rides_by_zone
from config import PARK_OPENING, PARK_CLOSING

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Disney Wait Time", page_icon="🏰", layout="centered")

# --- STYLE CSS (Inchangé) ---
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
    code { color: #ff9a9e !important; background: rgba(255,154,158,0.1) !important; }
    [data-testid='stMetricValue'] { font-size: 1.8rem; }
</style>
""", unsafe_allow_html=True)

# --- INITIALISATION ---
paris_tz = pytz.timezone('Europe/Paris')

if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = datetime.now(paris_tz).strftime("%H:%M:%S")

refresh_count = st_autorefresh(interval=60000, key="datarefresh")

if refresh_count > 0:
    st.session_state.last_refresh = datetime.now(paris_tz).strftime("%H:%M:%S")

supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def is_park_theoretically_open(current, opening, closing):
    if opening <= closing: return opening <= current <= closing
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
    st.write("Aucune donnée disponible pour le moment.")
    if st.button("Tenter de forcer un relevé maintenant"):
        if trigger_github_action() == 204:
            st.toast("🚀 Signal envoyé au robot !"); time.sleep(45); st.rerun()

heure_reset = maintenant.replace(hour=2, minute=30, second=0, microsecond=0)
debut_journee = heure_reset if maintenant >= heure_reset else heure_reset - timedelta(days=1)

# --- SECTION BOUTONS ---
col_btn1, col_btn2 = st.columns(2)
with col_btn1:
    if st.button('🔄 Rafraîchir l\'Affichage'): st.rerun()
with col_btn2:
    if st.button('🚀 Forcer un Relevé Robot'):
        if trigger_github_action() == 204: st.toast("🚀 Robot lancé !"); time.sleep(45); st.rerun()

# --- RÉCUPÉRATION DES DONNÉES (Architecture State Machine) ---
try:
    # 1. Lecture de la table LIVE (Mise à jour par actualisation de ligne)
    resp_live = supabase.table("disney_live").select("*").execute()
    df_live = pd.DataFrame(resp_live.data)
    
    # 2. Lecture des pannes du jour
    resp_101 = supabase.table("logs_101").select("*").gte("start_time", debut_journee.isoformat()).execute()
    df_pannes = pd.DataFrame(resp_101.data)

    # 3. Lecture des statuts d'ouverture quotidienne
    resp_status = supabase.table("daily_status").select("*").execute()
    status_map = {item['ride_name']: item['has_opened_today'] for item in resp_status.data} if resp_status.data else {}
except Exception as e:
    st.error(f"Erreur Supabase : {e}")
    df_live, df_pannes, status_map = pd.DataFrame(), pd.DataFrame(), {}

if not df_live.empty:
    # --- LOGIQUE PARC FERMÉ ---
    parc_theoriquement_ouvert = is_park_theoretically_open(heure_actuelle, PARK_OPENING, PARK_CLOSING)
    parc_actuellement_ferme = not parc_theoriquement_ouvert
    
    # On récupère l'heure de la dernière mise à jour globale présente dans la table live
    df_live['updated_at'] = pd.to_datetime(df_live['updated_at']).dt.tz_convert('Europe/Paris')
    derniere_maj = df_live['updated_at'].max().strftime("%H:%M:%S")
    toutes_attractions = sorted(df_live['ride_name'].unique())

    # --- PRÉPARATION DES PANNES ---
    all_pannes = []
    if not df_pannes.empty:
        for _, row in df_pannes.iterrows():
            d = pd.to_datetime(row['start_time']).astimezone(paris_tz)
            f = pd.to_datetime(row['end_time']).astimezone(paris_tz) if pd.notna(row['end_time']) else None
            all_pannes.append({
                "ride": row['ride_name'], "debut": d, "fin": f,
                "duree": int((f - d).total_seconds() / 60) if f else 0,
                "statut": "EN_COURS" if f is None else "TERMINEE"
            })

    # --- FILTRES ---
    st.write("---")
    sc = st.text_input("Raccourci...", placeholder="ex: *FANTASY", label_visibility="collapsed")
    
    current_selection = st.query_params.get_all("fav")
    if sc.startswith("*"):
        shortcut_selection = get_rides_by_zone(sc, toutes_attractions, all_pannes)
        if shortcut_selection: current_selection = shortcut_selection

    valid_default = [item for item in current_selection if item in toutes_attractions]
    selected_options = st.multiselect("Attractions suivies :", options=toutes_attractions, default=valid_default, format_func=lambda x: f"{get_emoji(x)} {x}")
    st.query_params["fav"] = selected_options
    
    st.caption(f"🕒 Donnée : {derniere_maj} | Refresh : {st.session_state.last_refresh}")

    if parc_actuellement_ferme:
        st.info(f"ℹ️ Le parc est fermé ({PARK_OPENING} -> {PARK_CLOSING}).")

    # --- AFFICHAGE DES ATTRACTIONS ---
    if selected_options:
        st.divider()
        for ride in selected_options:
            ride_data = df_live[df_live['ride_name'] == ride]
            
            if not ride_data.empty:
                current = ride_data.iloc[0]
                a_deja_ouvert = status_map.get(ride, False)
                panne_actuelle = next((p for p in all_pannes if p['ride'] == ride and p['statut'] == "EN_COURS"), None)
                
                st.subheader(f"{get_emoji(ride)} {ride}")
                c1, c2 = st.columns(2)
        
                # 1. PARC FERMÉ
                if parc_actuellement_ferme:
                    c1.error("🔴 PARC FERMÉ")
                    c2.metric("Attente", "- - -")
        
                # 2. PAS ENCORE OUVERT AUJOURD'HUI
                elif not a_deja_ouvert:
                    c1.info("🕒 FERMÉ")
                    c2.metric("Attente", "- - -")
                    st.caption("⏳ En attente de l'ouverture officielle.")
        
                # 3. INTERRUPTION / 101
                elif panne_actuelle or not current['is_open']:
                    c1.warning("🔴 INTERRUPTION / 101")
                    if panne_actuelle:
                        min_inc = int((maintenant - panne_actuelle['debut']).total_seconds() / 60)
                        st.caption(f"⚠️ En panne depuis **{max(0, min_inc)} min**")
                    c2.metric("Attente", "- - -")
        
                # 4. OUVERT
                else:
                    c1.success("🟢 OUVERT")
                    c2.metric("Attente", f"{int(current['wait_time'])} min")

                # HISTORIQUE DES PANNES
                with st.expander("📜 Historique des pannes"):
                    h_pannes = [p for p in all_pannes if p['ride'] == ride and p['statut'] == "TERMINEE"]
                    if h_pannes:
                        for p in sorted(h_pannes, key=lambda x: x['debut'], reverse=True):
                            st.write(f"• De {p['debut'].strftime('%H:%M')} à {p['fin'].strftime('%H:%M')} ({p['duree']} min)")
                    else: st.write("✅ Aucune panne terminée aujourd'hui.")
                st.divider()

    # --- FLUX DES DERNIÈRES PANNES ---
    st.subheader("🚨 Dernières interruptions")
    if not df_pannes.empty:
        df_pannes['start_time_dt'] = pd.to_datetime(df_pannes['start_time'])
        flux_clean = df_pannes[df_pannes['start_time_dt'] >= debut_journee].sort_values('start_time', ascending=False).head(5)
        if not flux_clean.empty:
            for _, p in flux_clean.iterrows():
                d = pd.to_datetime(p['start_time']).astimezone(paris_tz)
                if pd.isna(p['end_time']): st.error(f"🔴 {p['ride_name']} >> depuis {d.strftime('%H:%M')}")
                else:
                    f = pd.to_datetime(p['end_time']).astimezone(paris_tz)
                    dur = int((f - d).total_seconds() / 60)
                    st.success(f"✅ {p['ride_name']} >> fini à {f.strftime('%H:%M')} ({dur} min)")
        else: st.write("✅ Aucune interruption réelle détectée.")
    else: st.write("✅ Aucune interruption détectée.")

else: st.warning("📭 Aucune donnée live disponible.")

# --- GESTION POPUP ---
if df_live.empty and "popup_shown" not in st.session_state:
    st.session_state.popup_shown = True
    popup_alerte_donnees()
elif not df_live.empty:
    if "popup_shown" in st.session_state: del st.session_state.popup_shown

st.divider()
st.caption("Disney Wait Time Tool | Real-time Dashboard")
