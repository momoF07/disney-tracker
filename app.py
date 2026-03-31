import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime, timedelta
import pytz
import requests
import time
from streamlit_autorefresh import st_autorefresh 
from emojis import get_emoji

# --- CONFIGURATION ---
st.set_page_config(page_title="Disney Live Control", page_icon="🏰", layout="centered")

# --- CONNEXION SUPABASE ---
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

# --- REFRESH ---
st_autorefresh(interval=60000, key="datarefresh")
paris_tz = pytz.timezone('Europe/Paris')

# --- LOGIQUE TEMPORELLE ---
maintenant = datetime.now(paris_tz)
heure_reset = maintenant.replace(hour=2, minute=0, second=0, microsecond=0)
if maintenant < heure_reset:
    debut_journee = heure_reset - timedelta(days=1)
else:
    debut_journee = heure_reset

# On demande à Supabase les données brutes (UTC par défaut sur leurs serveurs)
# On prend une marge de 4h pour être certain d'englober le reset de 2h du mat
query_date = (debut_journee - timedelta(hours=4)).isoformat()

# --- FONCTION ROBOT ---
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

if st.button('🔄 Actualiser & Forcer un Relevé'):
    with st.spinner("Signal envoyé au robot..."):
        if trigger_github_action() == 204:
            st.toast("🚀 Robot lancé !"); time.sleep(45); st.rerun()

# --- RÉCUPÉRATION ---
try:
    response = supabase.table("disney_logs").select("*").gte("created_at", query_date).order("created_at", desc=False).execute()
    df_raw = pd.DataFrame(response.data)
except Exception as e:
    st.error(f"Erreur Supabase : {e}")
    df_raw = pd.DataFrame()

if not df_raw.empty:
    # --- FIX CRITIQUE DU DÉCALAGE HORAIRE ---
    # 1. On convertit en datetime
    df_raw['created_at'] = pd.to_datetime(df_raw['created_at'], utc=True)
    # 2. On passe en heure de Paris (+2h actuellement)
    df_raw['created_at'] = df_raw['created_at'].dt.tz_convert('Europe/Paris')
    
    # Filtrage : Uniquement ce qui appartient à la journée commencée à 2h du mat
    df = df_raw[df_raw['created_at'] >= debut_journee].copy()
    
    if not df.empty:
        derniere_maj = df['created_at'].max().strftime("%H:%M:%S")
        toutes_attractions = sorted(df['ride_name'].unique())
        
        selected_options = st.multiselect(
            "Attractions :", options=toutes_attractions, 
            default=st.query_params.get_all("fav"),
            format_func=lambda x: f"{get_emoji(x)} {x}"
        )
        st.query_params["fav"] = selected_options
        st.caption(f"🕒 Dernière donnée (Heure Paris) : {derniere_maj}")

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
                        c1.error("🔴 FERMÉ")
                    st.divider()
    else:
        st.warning(f"⚠️ Aucune donnée après {debut_journee.strftime('%H:%M')}. (Dernière trouvée en base : {df_raw['created_at'].max().strftime('%H:%M')})")
else:
    st.warning("📭 La base de données ne renvoie rien pour le moment.")

st.markdown("<style>[data-testid='stMetricValue'] { font-size: 1.8rem; } .stButton button { width: 100%; border-radius: 10px; }</style>", unsafe_allow_html=True)
