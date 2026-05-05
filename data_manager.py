# data_manager.py
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

@st.cache_data(ttl=300)
def get_live_wait_times(_supabase):
    """Récupère tous les temps d'attente actuels[cite: 3]"""
    try:
        res = _supabase.table("disney_live").select("*").execute()
        return {item["ride_name"]: item for item in res.data}
    except: return {}

@st.cache_data(ttl=3600)
def get_park_schedule(_supabase, date_str):
    """Récupère les horaires des parcs pour une date donnée[cite: 3]"""
    try:
        res = _supabase.table("park_schedule").select("*").eq("date", date_str).execute()
        return res.data
    except: return []

def get_weather():
    """Récupère la météo (Simulation pour Marne-la-Vallée)[cite: 3]"""
    return {"temp": 12, "status": "Ciel Étoilé", "icon": "✨"}

@st.cache_data(ttl=600)
def get_ride_history_24h(_supabase, ride_name):
    """Historique précis pour le graphique sous l'attraction[cite: 3]"""
    try:
        limit = (datetime.now() - timedelta(hours=24)).isoformat()
        res = _supabase.table("ride_history").select("wait_time, last_updated").eq("ride_name", ride_name).gte("last_updated", limit).order("last_updated").execute()
        if not res.data: return pd.DataFrame()
        df = pd.DataFrame(res.data)
        paris_tz = pytz.timezone("Europe/Paris")
        df['last_updated'] = pd.to_datetime(df['last_updated']).dt.tz_convert(paris_tz)
        df['heure'] = df['last_updated'].dt.strftime('%H:%M')
        return df.rename(columns={"wait_time": "attente"})
    except: return pd.DataFrame()