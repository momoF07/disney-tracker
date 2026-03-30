import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
import pytz
import requests
import time

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Disney Live Control", page_icon="🎢", layout="centered")

# --- CONNEXION SUPABASE ---
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

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
st.title("🎢 Mes Favoris Disney")

# Bouton de mise à jour forcée
if st.button('🔄 Actualiser & Forcer un Relevé'):
    with st.spinner("Signal envoyé au robot... Patientez 40s."):
        status = trigger_github_action()
        if status == 204:
            st.toast("🚀 Robot lancé !", icon="✅")
            time.sleep(40)
            st.rerun()
        else:
            st.error(f"Erreur GitHub (Code {status})")

# --- RÉCUPÉRATION DES DONNÉES DU JOUR ---
paris_tz = pytz.timezone('Europe/Paris')
aujourd_hui = datetime.now(paris_tz).strftime("%Y-%m-%d")

try:
    response = supabase.table("disney_logs").select("*").gte("created_at", f"{aujourd_hui}T00:00:00").order("created_at", desc=True).execute()
    df = pd.DataFrame(response.data)
except:
    df = pd.DataFrame()

if not df.empty:
    df['created_at'] = pd.to_datetime(df['created_at']).dt.tz_convert('Europe/Paris')
    derniere_maj = df['created_at'].max().strftime("%H:%M:%S")
    
    # --- MENU DE SÉLECTION DES FAVORIS ---
    toutes_attractions = sorted(df['ride_name'].unique())
    
    # On crée une liste d'options avec emojis pour le menu
    options_menu = [f"❤️ {name}" for name in toutes_attractions]
    
    selected_options = st.multiselect(
        "Sélectionne tes attractions favorites :",
        options=options_menu,
        default=None,
        placeholder="Rechercher une attraction..."
    )
    
    # On nettoie les noms sélectionnés (on enlève le ❤️ pour matcher la base)
    selection = [name.replace("❤️ ", "") for name in selected_options]

    st.info(f"🕒 Dernier relevé : **{derniere_maj}**")
    st.divider()

    # --- AFFICHAGE DES SÉLECTIONNÉS ---
    if not selection:
        st.write("👆 Sélectionne des attractions ci-dessus pour les afficher ici.")
    else:
        for ride in selection:
            ride_df = df[df['ride_name'] == ride]
            if not ride_df.empty:
                last = ride_df.iloc[0]
                st.subheader(f"📍 {ride}")
                
                c1, c2 = st.columns(2)
                if last['is_open']:
                    c1.success("🟢 OUVERT")
                else:
                    c1.error("🔴 FERMÉ / PANNE")
                c2.metric("Attente", f"{last['wait_time']} min")
                
                # Calcul des pannes
                ride_sorted = ride_df.sort_values('created_at')
                ride_sorted['switched_off'] = (ride_sorted['is_open'] == False) & (ride_sorted['is_open'].shift(1) == True)
                nb_pannes = ride_sorted['switched_off'].sum()
                
                if nb_pannes > 0:
                    st.warning(f"⚠️ {nb_pannes} interruption(s) détectée(s) aujourd'hui.")
                st.divider()
else:
    st.warning("📭 Aucune donnée pour aujourd'hui. Cliquez sur le bouton pour lancer le relevé.")

# --- STYLE CSS ---
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 1.8rem; }
    .stButton button { width: 100%; border-radius: 10px; }
    /* Style pour le multiselect */
    .stMultiSelect div[data-baseweb="select"] {
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)
