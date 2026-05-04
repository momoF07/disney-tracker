# data_manager.py
import streamlit as st
from supabase import create_client

@st.cache_resource
def init_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def get_realtime_waits():
    # Logique pour récupérer les temps actuels
    pass

def get_monthly_stats(scope, target=None):
    # Logique SQL pour les statistiques sur 30 jours
    pass