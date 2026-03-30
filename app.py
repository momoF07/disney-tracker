import streamlit as st
import pandas as pd
from supabase import create_client

st.set_page_config(page_title="Disney Logs", page_icon="🎢")
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

st.title("📊 Historique des Pannes")

# Récupération des données
data = supabase.table("disney_logs").select("*").order("created_at", desc=True).limit(200).execute()
df = pd.DataFrame(data.data)

if not df.empty:
    df['created_at'] = pd.to_datetime(df['created_at']).dt.tz_convert('Europe/Paris')
    
    for ride in ["Big Thunder Mountain", "Phantom Manor", "Spider-Man W.E.B. Adventure"]:
        st.subheader(f"📍 {ride}")
        ride_df = df[df['ride_name'] == ride]
        
        # Calcul du nombre de pannes (changement de True à False)
        ride_df = ride_df.sort_values('created_at')
        ride_df['status_change'] = ride_df['is_open'].diff()
        nb_pannes = len(ride_df[ride_df['status_change'] == -1])
        
        c1, c2 = st.columns(2)
        c1.metric("Attente actuelle", f"{ride_df.iloc[-1]['wait_time']} min")
        c2.metric("Pannes aujourd'hui", nb_pannes)
        st.divider()
