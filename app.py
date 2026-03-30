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

# --- CONFIGURATION ---
st.set_page_config(page_title="Disney Dashboard", page_icon="🏰", layout="centered")
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
st_autorefresh(interval=60000, key="datarefresh")

def trigger_github_action():
    REPO, WORKFLOW_ID, TOKEN = "momoF07/disney-tracker", "check.yml", st.secrets["GITHUB_TOKEN"]
    url = f"https://api.github.com/repos/{REPO}/actions/workflows/{WORKFLOW_ID}/dispatches"
    headers = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try: res = requests.post(url, headers=headers, json={"ref": "main"}); return res.status_code
    except: return 500

st.title("🏰 My Disney Dashboard")
paris_tz = pytz.timezone('Europe/Paris')
maintenant = datetime.now(paris_tz)

if st.button('🔄 Forcer un relevé maintenant'):
    with st.spinner("Robot en cours..."):
        if trigger_github_action() == 204:
            st.toast("🚀 Lancé !"); time.sleep(40); st.rerun()

# Récupération des données
try:
    hier = maintenant - timedelta(hours=24)
    res = supabase.table("disney_logs").select("*").gte("created_at", hier.isoformat()).order("created_at", desc=True).execute()
    df = pd.DataFrame(res.data)
except: df = pd.DataFrame()

if not df.empty:
    df['created_at'] = pd.to_datetime(df['created_at']).dt.tz_convert('Europe/Paris')
    toutes = sorted(df['ride_name'].unique())
    favs = st.multiselect("Tes Favoris :", options=toutes, default=st.query_params.get_all("fav"), format_func=lambda x: f"{get_emoji(x)} {x}")
    st.query_params["fav"] = favs
    st.divider()

    for ride in favs:
        ride_df = df[df['ride_name'] == ride].sort_values('created_at', ascending=False)
        if not ride_df.empty:
            last = ride_df.iloc[0]
            st.subheader(f"{get_emoji(ride)} {ride}")
            c1, c2 = st.columns(2)
            wait = last['wait_time']
            if last['is_open']:
                c1.success("🟢 OUVERT"); c2.metric("Attente", f"{int(wait)} min")
            else:
                c1.error("🔴 FERMÉ"); c2.metric("Attente", "- - -")

            # --- LE GRAPHIQUE (LA CORRECTION EST ICI) ---
            if len(ride_df) > 1:
                four_h = maintenant - timedelta(hours=4)
                data = ride_df[ride_df['created_at'] >= four_h].copy()
                
                # On définit le dégradé de manière STRICTE
                # y1=1 (le haut du graphique à 80) / y2=0 (le bas à 0)
                gradient = alt.Gradient(
                    gradient='linear',
                    stops=[
                        alt.GradientStop(color='green', offset=0),      # 0 min
                        alt.GradientStop(color='green', offset=25/80),  # 25 min
                        alt.GradientStop(color='orange', offset=35/80), # 35 min
                        alt.GradientStop(color='orange', offset=55/80), # 55 min
                        alt.GradientStop(color='red', offset=65/80),    # 65 min
                        alt.GradientStop(color='red', offset=1)         # 80 min
                    ],
                    x1=0, x2=0, y1=1, y2=0 # Orientation verticale du bas (0) vers le haut (1)
                )

                base = alt.Chart(data).encode(
                    x=alt.X('created_at:T', title=None, axis=alt.Axis(format="%H:%M", grid=False)),
                    y=alt.Y('wait_time:Q', title=None, scale=alt.Scale(domain=[0, 80]), axis=alt.Axis(grid=True))
                )

                area = base.mark_area(color=gradient, opacity=0.8, interpolate='monotone')
                line = base.mark_line(color='#1f77b4', strokeWidth=2, interpolate='monotone')
                
                st.altair_chart((area + line).properties(height=200).interactive(False), use_container_width=True, theme=None)
            st.divider()

st.markdown("<style>[data-testid='stMetricValue'] { font-size: 1.8rem; } .stButton button { width: 100%; border-radius: 10px; }</style>", unsafe_allow_html=True)
