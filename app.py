import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime, timedelta
import pytz
import requests
import time
from streamlit_autorefresh import st_autorefresh 
from emojis import get_emoji 

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Disney Live Control", page_icon="🏰", layout="centered")

# --- CONNEXION SUPABASE ---
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

# --- ACTUALISATION AUTOMATIQUE ---
st_autorefresh(interval=30000, key="datarefresh")

# --- FONCTION POUR GITHUB ---
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

if st.button('🔄 Actualiser & Forcer un Relevé'):
    with st.spinner("Signal envoyé au robot..."):
        status = trigger_github_action()
        if status == 204:
            st.toast("🚀 Robot lancé !", icon="✅")
            time.sleep(40) 
            st.rerun()

# --- RÉCUPÉRATION DES DONNÉES (24h) ---
try:
    hier = maintenant - timedelta(hours=24)
    response = supabase.table("disney_logs") \
        .select("*") \
        .gte("created_at", hier.isoformat()) \
        .order("created_at", desc=False) \
        .execute()
    df = pd.DataFrame(response.data)
except:
    df = pd.DataFrame()

if not df.empty:
    df['created_at'] = pd.to_datetime(df['created_at']).dt.tz_convert('Europe/Paris')
    derniere_maj = df['created_at'].max().strftime("%H:%M:%S")

    # --- FLUX GLOBAL DES PANNES ---
    st.subheader("🚨 Flux des dernières pannes")
    
    all_pannes = []
    for ride_name in df['ride_name'].unique():
        ride_data = df[df['ride_name'] == ride_name].sort_values('created_at')
        en_panne = False
        debut_panne = None
        
        for i, row in ride_data.iterrows():
            if not row['is_open'] and not en_panne:
                en_panne = True
                debut_panne = row['created_at']
            elif row['is_open'] and en_panne:
                fin_panne = row['created_at']
                all_pannes.append({
                    "ride": ride_name, "debut": debut_panne, "fin": fin_panne,
                    "duree": int((fin_panne - debut_panne).total_seconds() / 60),
                    "statut": "TERMINEE"
                })
                en_panne = False
        
        if en_panne:
            all_pannes.append({"ride": ride_name, "debut": debut_panne, "fin": None, "statut": "EN_COURS"})

    # Affichage rapide du flux (5 derniers événements)
    flux_pannes = sorted(all_pannes, key=lambda x: x['debut'], reverse=True)[:5]
    for p in flux_pannes:
        if p['statut'] == "EN_COURS":
            st.error(f"🔴 **{p['ride']}** est tombé en panne à {p['debut'].strftime('%H:%M')}")
        else:
            st.info(f"✅ **{p['ride']}** a rouvert à {p['fin'].strftime('%H:%M')} ({p['duree']} min)")
    
    st.divider()

    # --- FAVORIS ---
    toutes_attractions = sorted(df['ride_name'].unique())
    selected_options = st.multiselect("Favoris :", options=toutes_attractions, default=st.query_params.get_all("fav"), format_func=lambda x: f"{get_emoji(x)} {x}")
    st.query_params["fav"] = selected_options

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

                # RECHERCHE DES PANNES POUR CETTE ATTRACTION
                ride_pannes = [p for p in all_pannes if p['ride'] == ride]
                
                # 1. BLOC JAUNE (Si en panne actuellement)
                panne_actuelle = next((p for p in ride_pannes if p['statut'] == "EN_COURS"), None)
                if panne_actuelle:
                    diff = maintenant - panne_actuelle['debut']
                    min_encours = int(diff.total_seconds() / 60)
                    st.warning(f"⚠️ En panne depuis {min_encours} min (à {panne_actuelle['debut'].strftime('%H:%M')})")

                # 2. HISTORIQUE (Expander)
                if ride_pannes:
                    with st.expander("📜 Historique des pannes"):
                        for p in reversed(ride_pannes):
                            if p['statut'] == "TERMINEE":
                                st.write(f"• Panne de {p['debut'].strftime('%H:%M')} à {p['fin'].strftime('%H:%M')} ({p['duree']} min)")
                            else:
                                diff_encours = int((maintenant - p['debut']).total_seconds() / 60)
                                st.write(f"• ⚠️ **En cours** : depuis {p['debut'].strftime('%H:%M')} (soit {diff_encours} min)")
                st.divider()
else:
    st.warning("📭 Aucune donnée disponible.")

st.markdown("<style>[data-testid='stMetricValue'] { font-size: 1.8rem; } .stButton button { width: 100%; border-radius: 10px; }</style>", unsafe_allow_html=True)
