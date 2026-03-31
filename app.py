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

# --- STYLE CSS POPUP ---
st.markdown("""
<style>
    [data-testid="stPopoverBody"] {
        position: fixed !important; top: 50% !important; left: 50% !important;
        transform: translate(-50%, -50%) !important; width: 85vw !important;
        max-width: 650px !important; background-color: rgba(17, 20, 28, 0.9) !important;
        backdrop-filter: blur(15px) !important; border-radius: 20px !important;
        padding: 20px !important; z-index: 999999 !important;
    }
    .shortcut-card { background: rgba(255, 255, 255, 0.05); border-radius: 10px; padding: 8px; margin-top: 10px; }
    .title-blue { color: #4facfe; font-weight: bold; }
    .title-green { color: #00f2fe; font-weight: bold; }
    .title-orange { color: #f9d423; font-weight: bold; }
    [data-testid='stMetricValue'] { font-size: 1.8rem; }
    .stButton button { width: 100%; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# --- INITIALISATION ---
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

# --- LOGIQUE TEMPORELLE ---
maintenant_paris = datetime.now(paris_tz)
# Reset à 2h du mat Paris = 00h00 Supabase (UTC)
heure_reset_paris = maintenant_paris.replace(hour=2, minute=0, second=0, microsecond=0)
debut_journee_paris = heure_reset_paris - timedelta(days=1) if maintenant_paris < heure_reset_paris else heure_reset_paris

# On convertit le début de journée en format "Brut Supabase" (UTC)
# On retire simplement 2 heures à l'heure de Paris
debut_query_supabase = (debut_journee_paris - timedelta(hours=2)).replace(tzinfo=None)

# --- INTERFACE ---
st.title("🏰 Disney Wait Time")

if st.button('🔄 Actualiser & Forcer un Relevé'):
    with st.spinner("Signal envoyé..."):
        if trigger_github_action() == 204:
            st.toast("🚀 Robot lancé !"); time.sleep(45); st.rerun()

# --- RÉCUPÉRATION DES DONNÉES ---
try:
    response = supabase.table("disney_logs")\
        .select("*")\
        .gte("created_at", debut_query_supabase.isoformat())\
        .order("created_at", desc=False)\
        .execute()
    df = pd.DataFrame(response.data)
except Exception as e:
    st.error(f"Erreur Supabase : {e}")
    df = pd.DataFrame()

if not df.empty:
    # On transforme en datetime
    df['created_at'] = pd.to_datetime(df['created_at'])
    
    # SI la donnée a déjà un fuseau (aware), on convertit. 
    # SINON (naive), on localise en UTC puis on convertit.
    if df['created_at'].dt.tz is not None:
        df['created_at'] = df['created_at'].dt.tz_convert('Europe/Paris')
    else:
        df['created_at'] = df['created_at'].dt.tz_localize('UTC').dt.tz_convert('Europe/Paris')
    
    # Exclusion Maintenance : 2h-8h Paris
    df = df[~((df['created_at'].dt.hour >= 2) & (df['created_at'].dt.hour < 8))].copy()


if not df.empty:
    # On transforme les dates de la base en Heure de Paris (+2h) pour l'affichage utilisateur
    df['created_at'] = pd.to_datetime(df['created_at']).dt.tz_localize('UTC').dt.tz_convert('Europe/Paris')
    
    # Exclusion Maintenance : 2h-8h Paris (soit 00h-06h Supabase)
    df = df[~((df['created_at'].dt.hour >= 2) & (df['created_at'].dt.hour < 8))].copy()
    
    if not df.empty:
        derniere_maj = df['created_at'].max().strftime("%H:%M:%S")
        toutes_attractions = sorted(df['ride_name'].unique())
        all_pannes = []

        # Calcul Pannes
        for ride_name in toutes_attractions:
            ride_data = df[df['ride_name'] == ride_name].sort_values('created_at')
            en_panne, debut_panne = False, None
            for i, row in ride_data.iterrows():
                if not row['is_open'] and not en_panne:
                    en_panne, debut_panne = True, row['created_at']
                elif row['is_open'] and en_panne:
                    all_pannes.append({"ride": ride_name, "debut": debut_panne, "fin": row['created_at'], "duree": int((row['created_at'] - debut_panne).total_seconds() / 60), "statut": "TERMINEE"})
                    en_panne = False
            if en_panne:
                all_pannes.append({"ride": ride_name, "debut": debut_panne, "fin": None, "statut": "EN_COURS"})

        # --- RACCOURCIS ---
        st.write("---")
        col_sc, col_help = st.columns([0.88, 0.12])
        with col_help:
            with st.popover("❓"):
                st.markdown("### 🔍 Raccourcis")
                st.markdown('<div class="shortcut-card"><p class="title-blue">🎡 Parcs</p></div>', unsafe_allow_html=True)
                cp1, cp2, cp3 = st.columns(3)
                cp1.code("*ALL"); cp2.code("*DLP"); cp3.code("*DAW")
                # (Reste de la popup inchangé...)

        with col_sc:
            sc = st.text_input("Raccourci :", placeholder="ex: *FANTASY...", label_visibility="collapsed")
        
        current_selection = st.query_params.get_all("fav")
        if sc.startswith("*"):
            shortcut_selection = get_rides_by_zone(sc, toutes_attractions)
            if shortcut_selection: current_selection = shortcut_selection

        selected_options = st.multiselect("Attractions :", options=toutes_attractions, default=current_selection, format_func=lambda x: f"{get_emoji(x)} {x}")
        st.query_params["fav"] = selected_options
        st.caption(f"🕒 Donnée : {derniere_maj} | Refresh : {st.session_state.last_refresh}")

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
                        c1.error("🔴 FERMÉ")
                    
                    ride_pannes = [p for p in all_pannes if p['ride'] == ride]
                    panne_actuelle = next((p for p in ride_pannes if p['statut'] == "EN_COURS"), None)
                    if panne_actuelle:
                        diff = int((maintenant_paris - panne_actuelle['debut']).total_seconds() / 60)
                        st.warning(f"⚠️ Panne depuis {diff} min")
                    st.divider()

        st.subheader("🚨 Flux des pannes")
        for p in sorted(all_pannes, key=lambda x: x['debut'], reverse=True)[:5]:
            if p['statut'] == "EN_COURS": st.error(f"🔴 {p['ride']} ({p['debut'].strftime('%H:%M')})")
            else: st.info(f"✅ {p['ride']} rouvert ({p['fin'].strftime('%H:%M')})")
    else:
        st.warning("😴 Maintenance.")
else:
    st.warning("📭 Aucune donnée.")

st.markdown("<style>[data-testid='stMetricValue'] { font-size: 1.8rem; } .stButton button { width: 100%; border-radius: 10px; }</style>", unsafe_allow_html=True)
