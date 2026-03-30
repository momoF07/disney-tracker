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
st.title("🎢 Temps d'attente Disney")

# Bouton de mise à jour forcée
if st.button('🔄 Actualiser & Forcer un Relevé'):
    with st.spinner("Signal envoyé au robot... Patientez 30s."):
        status = trigger_github_action()
        if status == 204:
            st.toast("🚀 Robot lancé !", icon="✅")
            time.sleep(30)
            st.rerun()
        else:
            st.error(f"Erreur GitHub (Code {status})")

# --- RÉCUPÉRATION DES DONNÉES DU JOUR ---
paris_tz = pytz.timezone('Europe/Paris')
maintenant = datetime.now(paris_tz)
aujourd_hui = maintenant.strftime("%Y-%m-%d")

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
    options_menu = [f"❤️ {name}" for name in toutes_attractions]
    
    selected_options = st.multiselect(
        "Sélectionne tes attractions favorites :",
        options=options_menu,
        default=None,
        placeholder="Rechercher une attraction..."
    )
    
    selection = [name.replace("❤️ ", "") for name in selected_options]

    st.info(f"🕒 Dernier relevé global : **{derniere_maj}**")
    st.divider()

    # --- AFFICHAGE DES SÉLECTIONNÉS ---
    if not selection:
        st.write("👆 Sélectionne des attractions pour voir le détail.")
    else:
        for ride in selection:
            ride_df = df[df['ride_name'] == ride].sort_values('created_at', ascending=False)
            
            if not ride_df.empty:
                last = ride_df.iloc[0]
                st.subheader(f"📍 {ride}")
                
                c1, c2 = st.columns(2)
                
                # 1. Gestion de l'affichage du temps d'attente
                # Si NaN ou 0 quand c'est fermé, on affiche "- - -"
                wait = last['wait_time']
                wait_display = f"{int(wait)} min" if pd.notnull(wait) and last['is_open'] else "- - -"
                
                if last['is_open']:
                    c1.success("🟢 OUVERT")
                else:
                    c1.error("🔴 FERMÉ / PANNE")
                
                c2.metric("Attente", wait_display)
                
                # 2. Gestion détaillée des pannes
                ride_chrono = ride_df.sort_values('created_at')
                # On détecte le moment où is_open passe de True à False
                ride_chrono['panne_start'] = (ride_chrono['is_open'] == False) & (ride_chrono['is_open'].shift(1) == True)
                
                pannes = ride_chrono[ride_chrono['panne_start'] == True]
                
                if not last['is_open']:
                    # Si l'attraction est actuellement fermée, on cherche l'heure du début de la panne actuelle
                    derniere_ouverture = ride_chrono[ride_chrono['is_open'] == True].last_valid_index()
                    if derniere_ouverture is not None:
                        debut_panne = ride_chrono.loc[derniere_ouverture + 1:].iloc[0]['created_at']
                        duree = maintenant - debut_panne
                        heures, reste = divmod(duree.total_seconds(), 3600)
                        minutes, _ = divmod(reste, 60)
                        
                        temps_ecoule = f"{int(minutes)}min" if heures == 0 else f"{int(heures)}h {int(minutes)}min"
                        st.warning(f"⚠️ En panne depuis **{temps_ecoule}** (début à {debut_panne.strftime('%H:%M')})")
                
                # Historique des pannes passées (si déjà résolues aujourd'hui)
                nb_pannes_totales = len(pannes)
                if nb_pannes_totales > 0 and last['is_open']:
                    st.caption(f"ℹ️ {nb_pannes_totales} interruption(s) signalée(s) aujourd'hui.")
                
                st.divider()
else:
    st.warning("📭 Aucune donnée. Cliquez sur le bouton pour lancer le relevé.")

# --- STYLE CSS ---
st.markdown("<style>[data-testid='stMetricValue'] { font-size: 1.8rem; } .stButton button { width: 100%; }</style>", unsafe_allow_html=True)
