import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime, timedelta, time as dt_time
import pytz
import requests
import time
from streamlit_autorefresh import st_autorefresh 
from emojis import get_emoji, get_rides_by_zone
# --- IMPORTATION DE LA CONFIGURATION ---
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
    .blue-t { color: #4facfe; }
    .green-t { color: #00f2fe; }
    .orange-t { color: #f9d423; }
    [data-testid='stMetricValue'] { font-size: 1.8rem; }
    .stButton button { width: 100%; border-radius: 12px; }
</style>
""", unsafe_allow_html=True)

# --- INITIALISATION ---
paris_tz = pytz.timezone('Europe/Paris')
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
st_autorefresh(interval=60000, key="datarefresh")

# --- INTERFACE ---
st.title("🏰 Disney Wait Time")
maintenant = datetime.now(paris_tz)
heure_actuelle = maintenant.time()

# Reset des données à 2h du matin
heure_reset = maintenant.replace(hour=2, minute=0, second=0, microsecond=0)
debut_journee = heure_reset - timedelta(days=1) if maintenant < heure_reset else heure_reset

# Affichage de l'amplitude du jour
st.info(f"🕒 Horaires du jour : **{PARK_OPENING.strftime('%H:%M')} - {PARK_CLOSING.strftime('%H:%M')}**")

if st.button('🔄 Actualiser & Forcer un Relevé'):
    REPO, WORKFLOW_ID, TOKEN = "momoF07/disney-tracker", "check.yml", st.secrets["GITHUB_TOKEN"]
    url = f"https://api.github.com/repos/{REPO}/actions/workflows/{WORKFLOW_ID}/dispatches"
    headers = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github.v3+json"}
    with st.spinner("Signal envoyé..."):
        res = requests.post(url, headers=headers, json={"ref": "main"})
        if res.status_code == 204:
            st.toast("🚀 Robot lancé !"); time.sleep(45); st.rerun()

# --- RÉCUPÉRATION DES DONNÉES ---
try:
    response = supabase.table("disney_logs").select("*").order("created_at", desc=True).limit(3000).execute()
    df_raw = pd.DataFrame(response.data)
except:
    df_raw = pd.DataFrame()

if not df_raw.empty:
    df_raw['created_at'] = pd.to_datetime(df_raw['created_at']).dt.tz_localize('UTC').dt.tz_convert('Europe/Paris')
    df = df_raw[df_raw['created_at'] >= debut_journee].copy()
    
    if not df.empty:
        derniere_maj = df['created_at'].max().strftime("%H:%M:%S")
        all_pannes = []
        toutes_attractions = sorted(df['ride_name'].unique())
        
        # Détection globale de fermeture
        derniere_maj_time = df['created_at'].max()
        etat_actuel = df[df['created_at'] == derniere_maj_time]
        tous_fermes_globalement = not etat_actuel['is_open'].any()

        # Calcul des pannes
        for ride_name in toutes_attractions:
            ride_data = df[df['ride_name'] == ride_name].sort_values('created_at')
            en_panne, debut_panne = False, None
            for i, row in ride_data.iterrows():
                if not row['is_open'] and not en_panne and not (2 <= row['created_at'].hour < 8):
                    en_panne, debut_panne = True, row['created_at']
                elif row['is_open'] and en_panne:
                    all_pannes.append({"ride": ride_name, "debut": debut_panne, "fin": row['created_at'], "duree": int((row['created_at'] - debut_panne).total_seconds() / 60), "statut": "TERMINEE"})
                    en_panne = False
            if en_panne:
                all_pannes.append({"ride": ride_name, "debut": debut_panne, "fin": None, "statut": "EN_COURS"})

        # --- FILTRES ---
        sc = st.text_input("Raccourci...", placeholder="ex: *FANTASY", label_visibility="collapsed")
        current_selection = st.query_params.get_all("fav")
        if sc.startswith("*"):
            shortcut_selection = get_rides_by_zone(sc, toutes_attractions, all_pannes)
            if shortcut_selection: current_selection = shortcut_selection
        selected_options = st.multiselect("Suivi :", options=toutes_attractions, default=[i for i in current_selection if i in toutes_attractions], format_func=lambda x: f"{get_emoji(x)} {x}")
        st.query_params["fav"] = selected_options
        st.caption(f"🕒 Donnée : {derniere_maj}")

        # --- AFFICHAGE ---
        if selected_options:
            st.divider()
            for ride in selected_options:
                ride_df = df[df['ride_name'] == ride].sort_values('created_at', ascending=False)
                if not ride_df.empty:
                    last = ride_df.iloc[0]
                    a_deja_ouvert = ride_df['is_open'].any()
                    st.subheader(f"{get_emoji(ride)} {ride}")
                    c1, c2 = st.columns(2)
                    
                    # 1. SOIR (Après l'heure de config OU si tout est fermé)
                    if (heure_actuelle > PARK_CLOSING) or (tous_fermes_globalement and maintenant.hour >= 19):
                        c1.error("🔴 PARC FERMÉ")
                        c2.metric("Attente", "- - -")
                    # 2. MATIN (Avant l'heure de config OU si jamais ouvert)
                    elif (heure_actuelle < PARK_OPENING) or (not a_deja_ouvert):
                        c1.info("🕒 FERMÉ")
                        c2.metric("Attente", "- - -")
                    # 3. PANNE
                    elif not last['is_open']:
                        c1.warning("🔴 INTERRUPTION")
                        p_actuelle = next((p for p in all_pannes if p['ride'] == ride and p['statut'] == "EN_COURS"), None)
                        if p_actuelle:
                            st.caption(f"⚠️ Depuis **{int((maintenant - p_actuelle['debut']).total_seconds() / 60)} min**")
                        c2.metric("Attente", "101")
                    # 4. OUVERT
                    else:
                        c1.success("🟢 OUVERT")
                        c2.metric("Attente", f"{int(last['wait_time'])} min")
                    
                    # HISTORIQUE (Uniquement les pannes TERMINEES)
                    with st.expander("📜 Historique des pannes terminées"):
                        hist_pannes = [p for p in all_pannes if p['ride'] == ride and p['statut'] == "TERMINEE"]
                        if hist_pannes:
                            for p in reversed(hist_pannes):
                                st.write(f"• {p['debut'].strftime('%H:%M')} à {p['fin'].strftime('%H:%M')} ({p['duree']} min)")
                        else: st.write("✅ Pas de panne terminée aujourd'hui.")
                    st.divider()

        # Flux des dernières pannes (Top 5)
        st.subheader("🚨 Flux")
        for p in sorted(all_pannes, key=lambda x: x['debut'], reverse=True)[:5]:
            if p['statut'] == "EN_COURS": st.error(f"🔴 {p['ride']} >> {p['debut'].strftime('%H:%M')}")
            else: st.success(f"✅ {p['ride']} >> {p['fin'].strftime('%H:%M')} ({p['duree']} min)")

    else: st.warning("😴 Maintenance nocturne.")
else: st.warning("📭 Pas de données.")
