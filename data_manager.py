import streamlit as st
import pandas as pd
import pytz
from supabase import create_client
from datetime import datetime, timedelta, timezone

@st.cache_resource
def init_supabase():
    """Initialise la connexion à Supabase"""
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

@st.cache_data(ttl=300)
def get_live_wait_times(_supabase):
    """Récupère les temps d'attente en direct"""
    try:
        res = _supabase.table("disney_live").select("*").execute()
        return {item["ride_name"]: item for item in res.data}
    except: return {}

@st.cache_data(ttl=3600)
def get_park_schedule(_supabase, date_str):
    """Récupère le planning des parcs[cite: 3]"""
    try:
        res = _supabase.table("park_schedule").select("*").eq("date", date_str).execute()
        return res.data
    except: return []

@st.cache_data(ttl=60)
def get_upcoming_shows(_supabase):
    """Récupère les spectacles des 2 prochaines heures"""
    try:
        now = datetime.now(timezone.utc)
        future_limit = (now + timedelta(hours=2)).isoformat()
        res = _supabase.table("show_times") \
            .select("*") \
            .eq("is_performed", False) \
            .gte("start_time", now.isoformat()) \
            .lte("start_time", future_limit) \
            .order("start_time") \
            .execute()
        return res.data
    except: return []

def get_recent_logs(_supabase, limit=8):
    """Récupère les derniers incidents du flux d'activités[cite: 3]"""
    try:
        res = _supabase.table("logs_101") \
            .select("*") \
            .order("start_time", desc=True) \
            .limit(limit) \
            .execute()
        return res.data
    except: return []

@st.cache_data(ttl=600)
def get_ride_history_24h(_supabase, ride_name):
    """Historique des dernières 24h pour une attraction[cite: 3]"""
    try:
        limit = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
        res = _supabase.table("ride_history") \
            .select("wait_time, last_updated") \
            .eq("ride_name", ride_name) \
            .gte("last_updated", limit) \
            .order("last_updated") \
            .execute()
        if not res.data: return pd.DataFrame()
        df = pd.DataFrame(res.data)
        paris_tz = pytz.timezone("Europe/Paris")
        df['last_updated'] = pd.to_datetime(df['last_updated']).dt.tz_convert(paris_tz)
        df['heure'] = df['last_updated'].dt.strftime('%H:%M')
        return df.rename(columns={"wait_time": "attente"})
    except: return pd.DataFrame()

def get_weather():
    return {"temp": 12, "status": "Ciel Étoilé", "icon": "✨"}