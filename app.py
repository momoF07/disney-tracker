import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime, timedelta
import pytz
import requests
import time
from streamlit_autorefresh import st_autorefresh 
from emojis import get_emoji 
import altair as alt

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Disney Live Dashboard", page_icon="🏰", layout="centered")

# --- CONNEXION SUPABASE ---
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

# --- ACTUALISATION AUTOMATIQUE (60 secondes) ---
st_autorefresh(interval=60000, key="datarefresh")

# --- FONCTION POUR DÉCLENCHER LE ROBOT GITHUB ---
def trigger_github_action():
    REPO = "momoF07/disney-tracker" 
    WORKFLOW_ID = "check.yml"
    TOKEN = st.secrets["GITHUB_TOKEN"]
    url = f"https://api.github.com/repos/{REPO}/actions/workflows/{WORKFLOW_ID}/dispatches"
    headers = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        res = requests.post(url, headers=headers, json={"ref": "main"})
        return res.status_code
    except: return 500

# --- INTERFACE ---
st.title("🏰 My Disney Dashboard")

paris_tz = pytz.timezone('Europe/Paris')
maintenant = datetime.now(paris_tz)
aujourd_hui = maintenant.strftime("%Y-%m-%d")

if st.button('🔄 Forcer un relevé maintenant'):
    with st.spinner("Le robot analyse les parcs..."):
        status = trigger_github_action()
        if status == 204:
            st.toast("🚀 Robot lancé !", icon="✅")
            time.sleep(40) 
            st.rerun()

# Récupération des données
try:
    hier = maintenant - timedelta(hours=24)
    response = supabase.table("disney_logs").select("*").gte("created_at", hier.isoformat()).order("created_at", desc=True).execute()
    df = pd.DataFrame(response.data)
except:
    df = pd.DataFrame()

if not df.empty:
    df['created_at'] = pd.to_datetime(df['created_at']).dt.tz_convert('Europe/Paris')
    derniere_maj = df['created_at'].max().strftime("%H:%M:%S")
    
    toutes_attractions = sorted(df['ride_name'].unique())
    params = st.query_params.get_all("fav")
    selected_options = st.multiselect("Favoris :", options=toutes_attractions, default=params, format_func=lambda x: f"{get_emoji(x)} {x}")
    st.query_params["fav"] = selected_options

    st.caption(f"🕒 Dernière donnée : {derniere_maj}")
    st.divider()

    if selected_options:
        for ride in selected_options:
            ride_df = df[df['ride_name'] == ride].sort_values('created_at', ascending=False)
            if not ride_df.empty:
                last = ride_df.iloc[0]
                st.subheader(f"{get_emoji(ride)} {ride}")
                
                c1, c2 = st.columns(2)
                wait = last['wait_time']
                if last['is_open']:
                    c1.success("🟢 OUVERT")
                    c2.metric("Attente", f"{int(wait)} min")
                else:
                    c1.error("🔴 FERMÉ")
                    c2.metric("Attente", "- - -")

                # --- LE GRAPHIQUE CORRIGÉ ---
                if len(ride_df) > 1:
                    four_hours_ago = maintenant - timedelta(hours=4)
                    chart_data = ride_df[ride_df['created_at'] >= four_hours_ago].copy()
                    
                    # DÉGRADÉ : On définit les paliers exacts
                    # 25/80 = 0.31 | 55/80 = 0.68 | 60/80 = 0.75
                    gradient = alt.Gradient(
                        gradient='linear',
                        stops=[
                            alt.GradientStop(color='#26a641', offset=0),    # Vert à 0 min
                            alt.GradientStop(color='#26a641', offset=0.31), # Vert jusqu'à 25 min
                            alt.GradientStop(color='#ff9f1c', offset=0.35), # Orange dès 28 min
                            alt.GradientStop(color='#ff9f1c', offset=0.68), # Orange jusqu'à 55 min
                            alt.GradientStop(color='#ff4b2b', offset=0.75), # Rouge dès 60 min
                            alt.GradientStop(color='#ff4b2b', offset=1.0)   # Rouge à 80 min
                        ],
                        x1=1, x2=1, y1=0, y2=1 # Inversion pour que 0 soit en bas
                    )

                    base = alt.Chart(chart_data).encode(
                        x=alt.X('created_at:T', title=None, axis=alt.Axis(format="%H:%M", grid=False)),
                        y=alt.Y('wait_time:Q', title=None, scale=alt.Scale(domain=[0, 80]), axis=alt.Axis(grid=True))
                    )

                    area = base.mark_area(color=gradient, opacity=0.8, interpolate='monotone')
                    line = base.mark_line(color='#1f77b4', strokeWidth=2)

                    st.altair_chart((area + line).properties(height=200).interactive(False), use_container_width=True, theme=None)
                st.divider()
