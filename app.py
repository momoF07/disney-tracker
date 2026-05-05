import streamlit as st
import pandas as pd
import config as cfg
import pytz
from datetime import datetime, timezone
from ui_components import render_metric_row, render_activity_item
from data_manager import *
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Disney Tracker Pro", layout="wide")
st_autorefresh(interval=5 * 60 * 1000, key="datarefresh")
paris_tz = pytz.timezone("Europe/Paris")
supabase = init_supabase()
live_data = get_live_wait_times(supabase)

# --- HEADER ---
now_p = datetime.now(paris_tz)
today = now_p.date().isoformat()

res_sched = supabase.table("park_schedule").select("*").eq("park_id", "DLP").eq("date", today).execute()
hours_display = "Fermé"
if res_sched.data:
    s = res_sched.data[0]
    o = pd.to_datetime(s['opening_time']).astimezone(paris_tz).strftime("%H:%M")
    c = pd.to_datetime(s['closing_time']).astimezone(paris_tz).strftime("%H:%M")
    hours_display = f"🏰 {o}-{c}"

render_metric_row({"temp": 12, "status": "Ciel Étoilé"}, hours_display, {"name": "Show", "time": "20:00"})
st.divider()

# --- ATTRACTIONS ---
st.header("🎢 État des Attractions")
t1, t2 = st.tabs(["Disneyland Park", "Adventure World"])

def render_cards(park_key):
    for land, rides in cfg.PARKS_DATA[park_key].items():
        st.markdown(f"#### 📍 {land}")
        cols = st.columns(4)
        for i, r_name in enumerate(rides):
            data = live_data.get(r_name)
            with cols[i % 4]:
                with st.container(border=True):
                    if data:
                        st.markdown(f"**{r_name}**")
                        if data['is_open']:
                            c1, c2 = st.columns([2, 1])
                            c1.markdown(f"### {data['wait_time']} min")
                            with c2:
                                with st.popover("📈"):
                                    h_df = get_ride_history_24h(supabase, r_name)
                                    if not h_df.empty: st.line_chart(h_df.set_index("heure")["attente"])
                            st.progress(min(data['wait_time']/120, 1.0))
                        else: st.markdown("🔒 Fermé")
                    else: st.caption(f"{r_name} (Indispo)")

with t1: render_cards("Disneyland Park")
with t2: render_cards("Disney Adventure World")

st.divider()

# --- ANALYSE 30 JOURS ---
st.header("📊 Analyse de Performance (30j)")
scope = st.selectbox("Cible", ["Global", "DLP", "DAW", "Attraction"])
target = st.selectbox("Sélection", cfg.ALL_RIDES_LIST if scope == "Attraction" else [scope])

rides_to_analyze = cfg.ALL_RIDES_LIST if scope == "Global" else cfg.get_rides_by_zone(target, cfg.ALL_RIDES_LIST)

if rides_to_analyze:
    s30 = get_stats_30d(supabase, rides_to_analyze)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Pannes", s30['nb_pannes'])
    m2.metric("Durée Totale", f"{s30['total_duree']//60}h{s30['total_duree']%60}m")
    m3.metric("Moyenne Panne", f"{s30['moy_duree']} min")
    m4.metric("Attente Moyenne", f"{s30['attente_moy']} min")

    df_30j = get_stats_history_30d(supabase, rides_to_analyze)
    if not df_30j.empty: st.area_chart(df_30j.set_index("date")["wait_time"], height=250)