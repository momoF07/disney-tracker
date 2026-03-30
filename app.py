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

# --- ACTUALISATION AUTOMATIQUE (Toutes les 30 secondes) ---
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
st.title("🏰 Suivi Disney")

# Heure locale
paris_tz = pytz.timezone('Europe/Paris')
maintenant = datetime.now(paris_tz)
aujourd_hui = maintenant.strftime("%Y-%m-%d")

# Bouton de mise à jour forcée
if st.button('🔄 Actualiser manuellement'):
    with st.spinner("Signal envoyé au robot... Patientez 40s."):
        status = trigger_github_action()
        if status == 204:
            st.toast("🚀 Robot lancé ! Analyse en cours...", icon="✅")
            time.sleep(40) 
            st.rerun()
        else:
            st.error(f"Erreur GitHub (Code {status}).")

# --- RÉCUPÉRATION DES DONNÉES DU JOUR ---
try:
    response = supabase.table("disney_logs") \
        .select("*") \
        .gte("created_at", f"{aujourd_hui}T00:00:00") \
        .order("created_at", desc=True) \
        .execute()
    df = pd.DataFrame(response.data)
except:
    df = pd.DataFrame()

# --- LOGIQUE D'AFFICHAGE ---
if not df.empty:
    df['created_at'] = pd.to_datetime(df['created_at']).dt.tz_convert('Europe/Paris')
    derniere_maj = df['created_at'].max().strftime("%H:%M:%S")
    
    # --- GESTION DES FAVORIS (QUERY PARAMS) ---
    toutes_attractions = sorted(df['ride_name'].unique())
    # Récupère les favoris dans l'URL pour les garder au refresh
    params = st.query_params.get_all("fav")
    
    selected_options = st.multiselect(
        "Ajouter des attractions à mes favoris :",
        options=toutes_attractions,
        default=params,
        format_func=lambda x: f"{get_emoji(x)} {x}",
        placeholder="Rechercher une attraction..."
    )
    
    # Sauvegarde immédiate dans l'URL
    st.query_params["fav"] = selected_options

    st.caption(f"⏱️ Auto-refresh : {maintenant.strftime('%H:%M:%S')} | 🕒 Data : {derniere_maj}")
    st.divider()

    # --- AFFICHAGE DES FAVORIS ---
    if not selected_options:
        st.info("👆 Sélectionne tes attractions pour les suivre en direct.")
    else:
        for ride in selected_options:
            ride_df = df[df['ride_name'] == ride].sort_values('created_at', ascending=False)
            if not ride_df.empty:
                last = ride_df.iloc[0]
                emoji = get_emoji(ride)
                
                st.subheader(f"{emoji} {ride}")
                
                c1, c2 = st.columns(2)
                wait = last['wait_time']
                is_open = last['is_open']
                
                # Statut et Temps
                if is_open:
                    c1.success("🟢 OUVERT")
                    c2.metric("Attente", f"{int(wait)} min")
                else:
                    c1.error("🔴 FERMÉ / PANNE")
                    c2.metric("Attente", "- - -")
                
                # Calcul de la durée de panne
                if not is_open:
                    ride_chrono = ride_df.sort_values('created_at')
                    last_open = ride_chrono[ride_chrono['is_open'] == True].last_valid_index()
                    if last_open is not None:
                        # On prend le premier point de données après la dernière ouverture connue
                        try:
                            start_panne = ride_chrono.loc[last_open + 1:].iloc[0]['created_at']
                            diff = maintenant - start_panne
                            h, r = divmod(diff.total_seconds(), 3600)
                            m, _ = divmod(r, 60)
                            temps_txt = f"{int(m)}min" if h == 0 else f"{int(h)}h{int(m)}min"
                            st.warning(f"⚠️ En panne depuis {temps_txt} (à {start_panne.strftime('%H:%M')})")
                        except:
                            pass
                
                st.divider()
else:
    st.warning("📭 Aucune donnée pour aujourd'hui.")

# --- STYLE CSS ---
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 1.8rem; }
    .stButton button { width: 100%; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)
