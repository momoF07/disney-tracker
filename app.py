import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime

st.set_page_config(page_title="Disney Dash", page_icon="🎢")
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

st.title("📊 Rapport d'Incidents - DAW & DLP")

# 1. Récupération des données
response = supabase.table("disney_logs").select("*").order("created_at", desc=True).limit(500).execute()
df = pd.DataFrame(response.data)

if not df.empty:
    # Conversion du temps en heure française
    df['created_at'] = pd.to_datetime(df['created_at']).dt.tz_convert('Europe/Paris')
    
    for ride in ["Big Thunder Mountain", "Phantom Manor", "Spider-Man W.E.B. Adventure"]:
        st.header(f"📍 {ride}")
        ride_df = df[df['ride_name'] == ride].sort_values('created_at')
        
        if not ride_df.empty:
            # --- CALCUL DES PANNES ---
            # On détecte quand le statut change (True -> False)
            ride_df['switched_off'] = (ride_df['is_open'] == False) & (ride_df['is_open'].shift(1) == True)
            pannes = ride_df[ride_df['switched_off'] == True]
            nb_pannes = len(pannes)
            
            # --- AFFICHAGE METRICS ---
            last_status = ride_df.iloc[-1]['is_open']
            current_wait = ride_df.iloc[-1]['wait_time']
            
            c1, c2 = st.columns(2)
            c1.metric("Attente Actuelle", f"{current_wait} min")
            c2.metric("Pannes détectées", nb_pannes, delta="Alertes" if nb_pannes > 0 else None, delta_color="inverse")
            
            # --- JOURNAL DES INCIDENTS ---
            if nb_pannes > 0:
                with st.expander("Voir le détail des pannes"):
                    for _, row in pannes.iterrows():
                        st.warning(f"⚠️ Panne détectée vers {row['created_at'].strftime('%H:%M')}")
            else:
                st.success("✅ Aucune interruption majeure enregistrée.")
        
        st.divider()
else:
    st.info("En attente de la première analyse du robot GitHub...")
