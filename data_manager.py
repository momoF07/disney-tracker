# data_manager.py
import streamlit as st
import pandas as pd
import pytz
from supabase import create_client
from datetime import datetime, timedelta, timezone

@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"][cite: 3]
    key = st.secrets["SUPABASE_KEY"][cite: 3]
    return create_client(url, key)[cite: 3]

@st.cache_data(ttl=300)
def get_live_wait_times(_supabase):
    try:
        res = _supabase.table("disney_live").select("*").execute()[cite: 3]
        return {item["ride_name"]: item for item in res.data}[cite: 3]
    except: return {}

@st.cache_data(ttl=3600)
def get_park_schedule(_supabase, date_str):
    try:
        res = _supabase.table("park_schedule").select("*").eq("date", date_str).execute()[cite: 3]
        return res.data[cite: 3]
    except: return []

@st.cache_data(ttl=60)
def get_upcoming_shows(_supabase):
    """Récupère les spectacles des 2 prochaines heures"""
    try:
        now = datetime.now(timezone.utc)[cite: 5]
        future_limit = (now + timedelta(hours=2)).isoformat()[cite: 5]
        res = _supabase.table("show_times") \
            .select("*") \
            .eq("is_performed", False) \
            .gte("start_time", now.isoformat()) \
            .lte("start_time", future_limit) \
            .order("start_time") \
            .execute()[cite: 5]
        return res.data[cite: 5]
    except: return []

def get_recent_logs(_supabase, limit=8):
    try:
        res = _supabase.table("logs_101") \
            .select("*") \
            .order("start_time", desc=True) \
            .limit(limit) \
            .execute()[cite: 3]
        return res.data[cite: 3]
    except: return []

@st.cache_data(ttl=600)
def get_ride_history_24h(_supabase, ride_name):
    try:
        limit = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()[cite: 3]
        res = _supabase.table("ride_history").select("wait_time, last_updated").eq("ride_name", ride_name).gte("last_updated", limit).order("last_updated").execute()[cite: 3]
        if not res.data: return pd.DataFrame()[cite: 3]
        df = pd.DataFrame(res.data)[cite: 3]
        paris_tz = pytz.timezone("Europe/Paris")[cite: 3]
        df['last_updated'] = pd.to_datetime(df['last_updated']).dt.tz_convert(paris_tz)[cite: 3]
        df['heure'] = df['last_updated'].dt.strftime('%H:%M')[cite: 3]
        return df.rename(columns={"wait_time": "attente"})[cite: 3]
    except: return pd.DataFrame()

def get_weather():
    return {"temp": 12, "status": "Ciel Étoilé", "icon": "✨"}