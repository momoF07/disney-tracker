# data_manager.py
import streamlit as st
import pandas as pd
import pytz
from supabase import create_client

@st.cache_resource
def init_supabase():
    """Initialise la connexion à Supabase avec mise en cache"""
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

def get_live_wait_times(supabase):
    """Récupère tous les temps d'attente actuels"""
    try:
        res = supabase.table("disney_live").select("*").execute()
        # Transforme la liste en dictionnaire pour un accès rapide : { "Nom": {données} }
        return {item["ride_name"]: item for item in res.data}
    except Exception as e:
        st.error(f"Erreur lors de la récupération des temps : {e}")
        return {}

def get_recent_logs(supabase, limit=10):
    """Récupère les derniers incidents (pannes et réouvertures)"""
    try:
        res = supabase.table("logs_101") \
            .select("*") \
            .order("start_time", desc=True) \
            .limit(limit) \
            .execute()
        return res.data
    except Exception as e:
        return []

def get_stats_for_rides(supabase, ride_names):
    """Calcule les statistiques agrégées pour une liste d'attractions"""
    try:
        # 1. Total pannes et durée moyenne
        logs_res = supabase.table("logs_101") \
            .select("duration_minutes") \
            .in_("ride_name", ride_names) \
            .execute()
        
        durations = [l["duration_minutes"] for l in logs_res.data if l["duration_minutes"] is not None]
        total_101 = len(durations)
        avg_duration = round(sum(durations) / total_101) if total_101 > 0 else 0

        # 2. Moyenne d'attente actuelle
        live_res = supabase.table("disney_live") \
            .select("wait_time") \
            .in_("ride_name", ride_names) \
            .execute()
        
        waits = [r["wait_time"] for r in live_res.data]
        avg_wait = round(sum(waits) / len(waits)) if waits else 0

        return {
            "total_101": total_101,
            "avg_duration": avg_duration,
            "avg_wait": avg_wait
        }
    except Exception:
        return {"total_101": 0, "avg_duration": 0, "avg_wait": 0}

def get_ride_history(supabase, ride_name):
    """Récupère l'historique des temps d'attente pour le graphique"""
    try:
        # On récupère les données des dernières 24h
        # Note : Assure-toi d'avoir une table 'ride_history' alimentée par ton scraper
        res = supabase.table("ride_history") \
            .select("wait_time, last_updated") \
            .eq("ride_name", ride_name) \
            .order("last_updated", desc=False) \
            .execute()
        
        if not res.data:
            return pd.DataFrame()

        df = pd.DataFrame(res.data)
        
        # Conversion Heure de Paris pour l'affichage du graphique
        paris_tz = pytz.timezone("Europe/Paris")
        df['last_updated'] = pd.to_datetime(df['last_updated']).dt.tz_convert(paris_tz)
        
        # On prépare le format pour l'axe X
        df['Heure'] = df['last_updated'].dt.strftime('%H:%M')
        df = df.rename(columns={"wait_time": "Minutes"})
        
        return df[['Heure', 'Minutes']]
    except Exception as e:
        print(f"Erreur historique : {e}")
        return pd.DataFrame()