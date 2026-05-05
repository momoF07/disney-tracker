import streamlit as st
import pandas as pd
import pytz
from supabase import create_client
from datetime import datetime, timedelta

@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

@st.cache_data(ttl=300)
def get_live_wait_times(_supabase):
    try:
        res = _supabase.table("disney_live").select("*").execute()
        return {item["ride_name"]: item for item in res.data}
    except: return {}

def get_recent_logs(_supabase, limit=10):
    try:
        res = _supabase.table("logs_101").select("*").order("start_time", desc=True).limit(limit).execute()
        return res.data
    except: return []

@st.cache_data(ttl=3600)
def get_stats_30d(_supabase, ride_names):
    """Calcule les statistiques précises sur les 30 derniers jours"""
    try:
        start_date = (datetime.now() - timedelta(days=30)).isoformat()
        
        # Logs pannes
        logs = _supabase.table("logs_101").select("duration_minutes").in_("ride_name", ride_names).gte("start_time", start_date).execute()
        durations = [l["duration_minutes"] for l in logs.data if l["duration_minutes"] is not None]
        nb_pannes = len(durations)
        total_m = sum(durations)
        
        # Historique attentes
        hist = _supabase.table("ride_history").select("wait_time, last_updated").in_("ride_name", ride_names).gte("last_updated", start_date).execute()
        attente_moy = 0
        if hist.data:
            df = pd.DataFrame(hist.data)
            df['date'] = pd.to_datetime(df['last_updated']).dt.date
            attente_moy = round(df.groupby('date')['wait_time'].mean().mean())

        return {
            "nb_pannes": nb_pannes, "total_duree": total_m,
            "moy_duree": round(total_m / nb_pannes) if nb_pannes > 0 else 0,
            "attente_moy": attente_moy
        }
    except: return {"nb_pannes": 0, "total_duree": 0, "moy_duree": 0, "attente_moy": 0}

@st.cache_data(ttl=600)
def get_ride_history_24h(_supabase, ride_name):
    """Historique précis pour le graphique sous l'attraction"""
    try:
        res = _supabase.table("ride_history").select("wait_time, last_updated").eq("ride_name", ride_name).gte("last_updated", (datetime.now() - timedelta(hours=24)).isoformat()).order("last_updated").execute()
        if not res.data: return pd.DataFrame()
        df = pd.DataFrame(res.data)
        paris_tz = pytz.timezone("Europe/Paris")
        df['last_updated'] = pd.to_datetime(df['last_updated']).dt.tz_convert(paris_tz)
        df['heure'] = df['last_updated'].dt.strftime('%H:%M')
        return df.rename(columns={"wait_time": "attente"})
    except: return pd.DataFrame()

@st.cache_data(ttl=3600)
def get_stats_history_30d(_supabase, ride_names):
    """Moyennes quotidiennes pour le graphique de performance"""
    try:
        res = _supabase.table("ride_history").select("wait_time, last_updated").in_("ride_name", ride_names).gte("last_updated", (datetime.now() - timedelta(days=30)).isoformat()).execute()
        if not res.data: return pd.DataFrame()
        df = pd.DataFrame(res.data)
        df['date'] = pd.to_datetime(df['last_updated']).dt.date
        return df.groupby('date')['wait_time'].mean().reset_index()
    except: return pd.DataFrame()

def get_weather():
    """Récupère la météo réelle ou simulée pour Marne-la-Vallée"""
    # Tu pourras connecter une API réelle ici plus tard
    return {"temp": 12, "status": "Ciel Étoilé", "icon": "✨"}