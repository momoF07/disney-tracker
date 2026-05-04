import streamlit as st
import pandas as pd
import pytz
from supabase import create_client
from datetime import datetime, timedelta

@st.cache_resource
def init_supabase():
    """Initialise la connexion à Supabase avec mise en cache"""
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

@st.cache_data(ttl=300) # Mise en cache des temps d'attente pendant 5 minutes
def get_live_wait_times(_supabase):
    try:
        res = _supabase.table("disney_live").select("*").execute()
        return {item["ride_name"]: item for item in res.data}
    except Exception as e:
        st.error(f"Erreur : {e}")
        return {}

def get_ride_history(_supabase, ride_name):
    """Récupère l'historique des dernières 24h pour les graphiques"""
    try:
        res = _supabase.table("ride_history") \
            .select("wait_time, last_updated") \
            .eq("ride_name", ride_name) \
            .gte("last_updated", (datetime.now() - timedelta(hours=24)).isoformat()) \
            .order("last_updated", desc=False) \
            .execute()
        
        if not res.data: return pd.DataFrame()
        df = pd.DataFrame(res.data)
        paris_tz = pytz.timezone("Europe/Paris")
        df['last_updated'] = pd.to_datetime(df['last_updated']).dt.tz_convert(paris_tz)
        df['heure'] = df['last_updated'].dt.strftime('%H:%M')
        return df.rename(columns={"wait_time": "attente"})
    except Exception:
        return pd.DataFrame()

def get_weather():
    """Récupère la météo réelle de Marne-la-Vallée (Simulation préparée)"""
    # Tu pourras connecter une API comme OpenWeatherMap ici plus tard
    return {"temp": 15, "status": "Nuageux", "icon": "☁️"}