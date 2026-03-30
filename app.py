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

# --- CONFIGURATION DES FAVORIS ---
# Modifie cette liste pour afficher les attractions que tu veux voir
MES_FAVORIS = [
    "Big Thunder Mountain",
    "Phantom Manor",
    "Spider-Man W.E.B. Adventure",
    "Star Wars Hyperspace Mountain",
    "Avengers Assemble: Flight Force",
    "Ratatouille: L'Aventure Totalement Toquée de Rémy"
]

# --- FONCTION POUR DÉCLENCHER LE ROBOT GITHUB ---
def trigger_github_action():
    # Remplace bien par ton pseudo et nom de dépôt GitHub
    REPO = "momoF07/disney-tracker" 
    WORKFLOW_ID = "check.yml"
    TOKEN = st.secrets["GITHUB_TOKEN"] # Assure-toi d'avoir mis le ghp_... dans les secrets Streamlit
    
    url = f"https://api.github.com/repos/{REPO}/actions/workflows/{WORKFLOW_ID}/dispatches"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {"ref": "main"}
    
    try:
        res = requests.post(url, headers=headers, json=data)
        return res.status_code
    except:
        return 500

# --- INTERFACE UTILISATEUR ---
st.title("🎢 État des Attractions")

# Bouton de mise à jour forcée
if st.button('🔄 Actualiser & Forcer un Relevé'):
    with st.spinner("Signal envoyé au robot GitHub..."):
        status = trigger_github_action()
        if status == 204:
            st.toast("🚀 Robot lancé ! Mise à jour dans 10s...", icon="✅")
            time.sleep(45) # Laisse le temps au worker.py de finir
            st.rerun()
        else:
            st.error(f"Erreur GitHub (Code {status}). Vérifie ton GITHUB_TOKEN dans les secrets.")

# --- RÉCUPÉRATION DES DONNÉES DU JOUR ---
paris_tz = pytz.timezone('Europe/Paris')
maintenant = datetime.now(paris_tz)
aujourd_hui = maintenant.strftime("%Y-%m-%d")

try:
    # On récupère toutes les données de la journée
    response = supabase.table("disney_logs") \
        .select("*") \
        .gte("created_at", f"{aujourd_hui}T00:00:00") \
        .order("created_at", desc=True) \
        .execute()
    
    df = pd.DataFrame(response.data)
except Exception as e:
    st.error("Impossible de joindre la base de données.")
    df = pd.DataFrame()

# --- AFFICHAGE ---
if not df.empty:
    df['created_at'] = pd.to_datetime(df['created_at']).dt.tz_convert('Europe/Paris')
    
    # Heure du dernier relevé enregistré
    derniere_maj = df['created_at'].max().strftime("%H:%M:%S")
    st.info(f"🕒 Dernier relevé : **{derniere_maj}**")
    
    st.divider()

    # Boucle sur tes favoris uniquement
    for ride in MES_FAVORIS:
        ride_df = df[df['ride_name'] == ride]
        
        if not ride_df.empty:
            # On prend la ligne la plus récente (grâce au order desc=True)
            last = ride_df.iloc[0]
            
            st.subheader(f"📍 {ride}")
            
            c1, c2 = st.columns(2)
            
            # Affichage Statut
            if last['is_open']:
                c1.success("🟢 OUVERT")
            else:
                c1.error("🔴 FERMÉ / PANNE")
                
            # Affichage Attente
            c2.metric("Attente", f"{last['wait_time']} min")
            
            # Calcul des pannes sur la journée
            # On trie par ordre chronologique pour détecter les changements
            ride_sorted = ride_df.sort_values('created_at')
            ride_sorted['switched_off'] = (ride_sorted['is_open'] == False) & (ride_sorted['is_open'].shift(1) == True)
            nb_pannes = ride_sorted['switched_off'].sum()
            
            if nb_pannes > 0:
                st.warning(f"⚠️ {nb_pannes} interruption(s) détectée(s) aujourd'hui.")
            
            st.divider()
else:
    st.warning("📭 Aucune donnée pour aujourd'hui. Cliquez sur le bouton pour lancer le premier relevé.")

# --- CSS POUR MOBILE ---
st.markdown("""
    <style>
    /* Optimise l'affichage des metrics sur mobile */
    [data-testid="stMetricValue"] {
        font-size: 1.8rem;
    }
    </style>
    """, unsafe_allow_html=True)
