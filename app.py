import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime

st.set_page_config(page_title="Disney Check Time", page_icon="🎢")

# Connexion Supabase
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

st.title("📊 Rapport d'Incidents - DAW & DLP")

# 1. Récupération des données
response = supabase.table("disney_logs").select("*").order("created_at", desc=True).limit(500).execute()
df = pd.DataFrame(response.data)

if not df.empty:
    # Conversion du temps en heure française
    df['created_at'] = pd.to_datetime(df['created_at']).dt.tz_convert('Europe/Paris')
    
    # --- LISTE AUTOMATIQUE ---
    # On prend toutes les attractions présentes dans la base
    liste_attractions = sorted(df['ride_name'].unique())
    
    for ride in liste_attractions:
        st.header(f"📍 {ride}")
        
        # On crée le petit tableau spécifique à CETTE attraction
        ride_df = df[df['ride_name'] == ride].sort_values('created_at')
        
        # On vérifie s'il y a bien des données pour cette attraction
        if not ride_df.empty:
            # --- CALCUL DES PANNES ---
            # Détection du passage de True (ouvert) à False (fermé)
            ride_df['switched_off'] = (ride_df['is_open'] == False) & (ride_df['is_open'].shift(1) == True)
            pannes = ride_df[ride_df['switched_off'] == True]
            nb_pannes = len(pannes)
            
            # --- AFFICHAGE METRICS ---
            last_status = ride_df.iloc[-1]['is_open']
            current_wait = ride_df.iloc[-1]['wait_time']
            
            # Couleur du statut
            statut_texte = "🟢 OUVERT" if last_status else "🔴 EN PANNE / FERMÉ"
            st.subheader(statut_texte)
            
            c1, c2 = st.columns(2)
            c1.metric("Attente Actuelle", f"{current_wait} min")
            c2.metric("Pannes aujourd'hui", nb_pannes)
            
            # --- JOURNAL DES INCIDENTS ---
            if nb_pannes > 0:
                with st.expander("Voir le détail des pannes"):
                    for _, row in pannes.iterrows():
                        st.warning(f"⚠️ Coupure détectée vers {row['created_at'].strftime('%H:%M')}")
            else:
                st.success("✅ Aucune interruption majeure enregistrée.")
        
        st.divider()
else:
    st.info("🔄 En attente de la première analyse du robot GitHub...")
