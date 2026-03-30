import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
import pytz
import requests
import time

# Config
st.set_page_config(page_title="Disney Live Control", page_icon="🎢")
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

# --- FONCTION POUR LANCER LE ROBOT GITHUB ---
def trigger_github_action():
    # Remplace par ton pseudo et le nom de ton dépôt
    REPO = "momoF07/disney-tracker" 
    WORKFLOW_ID = "check.yml" # Le nom de ton fichier yaml
    TOKEN = st.secrets["GITHUB_TOKEN"]
    
    url = f"https://api.github.com/repos/{REPO}/actions/workflows/{WORKFLOW_ID}/dispatches"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {"ref": "main"}
    
    res = requests.post(url, headers=headers, json=data)
    return res.status_code

# --- INTERFACE ---
st.title("🎢 État des Attractions")

# Bouton Actualiser + Force Check
if st.button('🔄 Actualiser & Forcer un Relevé'):
    with st.spinner("Demande envoyée au robot GitHub..."):
        status = trigger_github_action()
        if status == 204:
            st.toast("🚀 Robot lancé ! Attente des données...", icon="✅")
            time.sleep(10) # On attend 10s que le robot finisse son travail
            st.rerun()
        else:
            st.error(f"Erreur lors du lancement du robot (Code {status})")

# --- RÉCUPÉRATION DES DONNÉES ---
paris_tz = pytz.timezone('Europe/Paris')
aujourd_hui = datetime.now(paris_tz).strftime("%Y-%m-%d")

response = supabase.table("disney_logs").select("*").gte("created_at", f"{aujourd_hui}T00:00:00").order("created_at", desc=True).execute()
df = pd.DataFrame(response.data)

if not df.empty:
    df['created_at'] = pd.to_datetime(df['created_at']).dt.tz_convert('Europe/Paris')
    st.info(f"🕒 Dernier relevé : **{df['created_at'].max().strftime('%H:%M:%S')}**")
    
    MON_CHOIX = ["Big Thunder Mountain", "Phantom Manor"]
    
    for ride in MON_CHOIX:
        ride_df = df[df['ride_name'] == ride]
        if not ride_df.empty:
            last = ride_df.iloc[0] # La plus récente
            
            st.subheader(f"📍 {ride}")
            c1, c2 = st.columns(2)
            
            etat = "🟢 OUVERT" if last['is_open'] else "🔴 FERMÉ / PANNE"
            c1.metric("Statut", etat)
            c2.metric("Attente", f"{last['wait_time']} min")
            
            # Calcul pannes rapides
            ride_sorted = ride_df.sort_values('created_at')
            ride_sorted['switched_off'] = (ride_sorted['is_open'] == False) & (ride_sorted['is_open'].shift(1) == True)
            nb_pannes = ride_sorted['switched_off'].sum()
            
            if nb_pannes > 0:
                st.warning(f"⚠️ {nb_pannes} interruption(s) détectée(s) aujourd'hui.")
            st.divider()
else:
    st.warning("Aucune donnée. Cliquez sur le bouton pour lancer le premier relevé.")
