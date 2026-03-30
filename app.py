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
st.set_page_config(page_title="Disney Live Control", page_icon="🏰", layout="centered")

# --- CONNEXION SUPABASE ---
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

# --- ACTUALISATION AUTOMATIQUE ---
st_autorefresh(interval=30000, key="datarefresh")

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

# --- INTERFACE UTILISATEUR ---
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
        else:
            st.error(f"Erreur GitHub (Code {status}).")

# --- RÉCUPÉRATION DES DONNÉES ---
try:
    response = supabase.table("disney_logs") \
        .select("*") \
        .gte("created_at", f"{aujourd_hui}T00:00:00") \
        .order("created_at", desc=False) \
        .execute()
    df = pd.DataFrame(response.data)
except:
    df = pd.DataFrame()

if not df.empty:
    df['created_at'] = pd.to_datetime(df['created_at']).dt.tz_convert('Europe/Paris')
    derniere_maj = df['created_at'].max().strftime("%H:%M:%S")
    
    toutes_attractions = sorted(df['ride_name'].unique())
    params = st.query_params.get_all("fav")
    
    selected_options = st.multiselect(
        "Ajouter des attractions à mes favoris :",
        options=toutes_attractions,
        default=params,
        format_func=lambda x: f"{get_emoji(x)} {x}"
    )
    st.query_params["fav"] = selected_options

    st.caption(f"⏱️ Auto-refresh : {maintenant.strftime('%H:%M:%S')} | 🕒 Data : {derniere_maj}")
    st.divider()

    if not selected_options:
        st.info("👆 Sélectionne tes attractions pour les suivre.")
    else:
        for ride in selected_options:
            # On trie par date ascendante pour l'analyse des pannes
            ride_df = df[df['ride_name'] == ride].sort_values('created_at')
            if not ride_df.empty:
                last = ride_df.iloc[-1]
                st.subheader(f"{get_emoji(ride)} {ride}")
                
                c1, c2 = st.columns(2)
                wait, is_open = last['wait_time'], last['is_open']
                
                if is_open:
                    c1.success("🟢 OUVERT")
                    c2.metric("Attente", f"{int(wait)} min")
                else:
                    c1.error("🔴 FERMÉ / PANNE")
                    c2.metric("Attente", "- - -")
                
                # --- LOGIQUE DU JOURNAL DES PANNES ---
                pannes_trouvees = []
                en_panne = False
                debut_panne = None
                
                for i, row in ride_df.iterrows():
                    # Détection début de panne (Ouvert -> Fermé)
                    if not row['is_open'] and not en_panne:
                        en_panne = True
                        debut_panne = row['created_at']
                    
                    # Détection fin de panne (Fermé -> Ouvert)
                    elif row['is_open'] and en_panne:
                        fin_panne = row['created_at']
                        duree = fin_panne - debut_panne
                        min_totaux = int(duree.total_seconds() / 60)
                        
                        pannes_trouvees.append({
                            "txt": f"Panne de {debut_panne.strftime('%H:%M')} à {fin_panne.strftime('%H:%M')}",
                            "duree": f"{min_totaux} min"
                        })
                        en_panne = False
                        debut_panne = None

                # Affichage de la panne en cours si elle existe
                if en_panne:
                    diff = maintenant - debut_panne
                    min_encours = int(diff.total_seconds() / 60)
                    st.warning(f"⚠️ En panne depuis {debut_panne.strftime('%H:%M')} ({min_encours} min)")

                # Affichage de la liste des pannes passées
                if pannes_trouvees:
                    with st.expander("📜 Historique des pannes du jour"):
                        for p in reversed(pannes_trouvees): # Les plus récentes en premier
                            st.write(f"• {p['txt']} (durée {p['duree']})")
                
                st.divider()
else:
    st.warning("📭 Aucune donnée pour aujourd'hui.")

st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 1.8rem; }
    .stButton button { width: 100%; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)
