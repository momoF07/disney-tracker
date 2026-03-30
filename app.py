import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
import pytz
import requests
import time
from streamlit_autorefresh import st_autorefresh 
from emojis import get_emoji 

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Disney Live Dashboard", page_icon="🏰", layout="centered")

# --- CONNEXION SUPABASE ---
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

# --- ACTUALISATION AUTOMATIQUE (60 secondes) ---
st_autorefresh(interval=60000, key="datarefresh")

# --- FONCTION POUR DÉCLENCHER LE ROBOT GITHUB ---
def trigger_github_action():
    REPO = "momoF07/disney-tracker" 
    WORKFLOW_ID = "check.yml"
    TOKEN = st.secrets["GITHUB_TOKEN"]
    url = f"https://api.github.com/repos/{REPO}/actions/workflows/{WORKFLOW_ID}/dispatches"
    headers = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        res = requests.post(url, headers=headers, json={"ref": "main"})
        return res.status_code
    except: return 500

# --- INTERFACE ---
st.title("🏰 My Disney Dashboard")

paris_tz = pytz.timezone('Europe/Paris')
maintenant = datetime.now(paris_tz)
aujourd_hui = maintenant.strftime("%Y-%m-%d")

if st.button('🔄 Forcer un relevé maintenant'):
    with st.spinner("Le robot analyse les parcs..."):
        status = trigger_github_action()
        if status == 204:
            st.toast("🚀 Robot lancé !", icon="✅")
            time.sleep(40) 
            st.rerun()

# Récupération des données Disney
try:
    response = supabase.table("disney_logs").select("*").gte("created_at", f"{aujourd_hui}T00:00:00").order("created_at", desc=True).execute()
    df = pd.DataFrame(response.data)
except:
    df = pd.DataFrame()

if not df.empty:
    df['created_at'] = pd.to_datetime(df['created_at']).dt.tz_convert('Europe/Paris')
    derniere_maj = df['created_at'].max().strftime("%H:%M:%S")
    
    toutes_attractions = sorted(df['ride_name'].unique())
    params = st.query_params.get_all("fav")
    
    selected_options = st.multiselect(
        "Mes attractions suivies :",
        options=toutes_attractions,
        default=params,
        format_func=lambda x: f"{get_emoji(x)} {x}"
    )
    st.query_params["fav"] = selected_options

    st.caption(f"🕒 Donnée : {derniere_maj} | Prochaine vérification auto dans 1 min")
    st.divider()

    if not selected_options:
        st.info("Sélectionne des attractions pour les afficher ici.")
    else:
        for ride in selected_options:
            ride_df = df[df['ride_name'] == ride].sort_values('created_at', ascending=False)
            if not ride_df.empty:
                last = ride_df.iloc[0]
                st.subheader(f"{get_emoji(ride)} {ride}")
                c1, c2 = st.columns(2)
                
                wait = last['wait_time']
                is_open = last['is_open']
                
                if is_open:
                    c1.success("🟢 OUVERT")
                    c2.metric("Attente", f"{int(wait)} min")
                else:
                    c1.error("🔴 FERMÉ / PANNE")
                    c2.metric("Attente", "- - -")
                
                if not is_open:
                    ride_chrono = ride_df.sort_values('created_at')
                    last_open = ride_chrono[ride_chrono['is_open'] == True].last_valid_index()
                    if last_open is not None:
                        start_panne = ride_chrono.loc[last_open + 1:].iloc[0]['created_at']
                        diff = maintenant - start_panne
                        h, r = divmod(diff.total_seconds(), 3600)
                        m, _ = divmod(r, 60)
                        txt = f"{int(m)}min" if h == 0 else f"{int(h)}h{int(m)}min"
                        st.warning(f"⚠️ En panne depuis {txt} (à {start_panne.strftime('%H:%M')})")
                st.divider()
else:
    st.warning("📭 Aucune donnée disponible.")

# CSS
st.markdown("<style>[data-testid='stMetricValue'] { font-size: 1.8rem; } .stButton button { width: 100%; }</style>", unsafe_allow_html=True)
