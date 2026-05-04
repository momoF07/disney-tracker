import streamlit as st
import pandas as pd
import config as cfg
import pytz
from datetime import datetime, timezone
from ui_components import render_metric_row, render_activity_item
from data_manager import init_supabase, get_live_wait_times, get_recent_logs, get_stats_for_rides
from streamlit_autorefresh import st_autorefresh

# 1. Configuration, UTC et Refresh (Toutes les 5 minutes)
st.set_page_config(page_title="Disney Tracker Pro", layout="wide", initial_sidebar_state="collapsed")
st_autorefresh(interval=5 * 60 * 1000, key="datarefresh")
paris_tz = pytz.timezone("Europe/Paris")

# 2. Initialisation Supabase
supabase = init_supabase()

# 3. Récupération des données Live
live_data = get_live_wait_times(supabase)

# --- 1. HEADER (Météo / Horaires / Shows) ---
st.title("🏰 Disney Live Control Center")

now_iso = datetime.now(timezone.utc).isoformat()
res_show = supabase.table("show_times") \
    .select("*") \
    .eq("is_performed", False) \
    .gte("start_time", now_iso) \
    .order("start_time") \
    .limit(1) \
    .execute()

next_show_data = {"name": "Aucun show", "time": "--:--"}
if res_show.data:
    s = res_show.data[0]
    # Conversion forcée vers l'heure de Paris
    dt_utc = pd.to_datetime(s['start_time'])
    dt_paris = dt_utc.astimezone(paris_tz)
    
    next_show_data = {
        "name": s['show_name'], 
        "time": dt_paris.strftime("%H:%M")
    }

render_metric_row(
    {"temp": 18, "status": "Ciel Dégagé"}, 
    "09:30 - 21:00", 
    next_show_data
)
st.divider()

# --- 2. TEMPS D'ATTENTE ---
st.header("🎢 Temps d'Attente")
tab_wait1, tab_wait2 = st.tabs(["Disneyland Park", "Disney Adventure World"])

def render_park_tab(park_key):
    for land, rides in cfg.PARKS_DATA[park_key].items():
        with st.expander(f"📍 {land}", expanded=True):
            cols = st.columns(4)
            for i, ride_name in enumerate(rides):
                data = live_data.get(ride_name)
                if data:
                    wait = data["wait_time"]
                    is_open = data["is_open"]
                    status_text = "Ouvert ✅" if is_open else "Fermé 🔴"
                    with cols[i % 4]:
                        st.metric(label=ride_name, value=f"{wait} min" if is_open else "---", 
                                  delta=status_text, delta_color="normal" if is_open else "inverse")
                else:
                    with cols[i % 4]: st.caption(f"⌛ {ride_name}\n(Indisponible)")

with tab_wait1: render_park_tab("Disneyland Park")
with tab_wait2: render_park_tab("Disney Adventure World")

st.divider()

# --- 3. AGENDA DES SPECTACLES (NOUVEAU) ---
st.header("🎭 Agenda des Spectacles")
tab_show1, tab_show2 = st.tabs(["Disneyland Park", "Disney Adventure World"])

def render_shows(park_code):
    # Récupération de tous les shows du jour pour le parc
    res = supabase.table("show_times") \
        .select("*") \
        .eq("park", park_code) \
        .order("start_time") \
        .execute()
    
    if not res.data:
        st.info("Aucun horaire de spectacle disponible pour le moment.")
        return

    # Groupement par nom de show pour l'affichage
    df_shows = pd.DataFrame(res.data)
    unique_shows = df_shows['show_name'].unique()
    
    cols = st.columns(3)
    for i, name in enumerate(unique_shows):
        show_perf = df_shows[df_shows['show_name'] == name]
        
        # Trouver la prochaine performance
        future_perf = show_perf[show_perf['is_performed'] == False]
        
        if not future_perf.empty:
            # Conversion Heure de Paris pour le "Value"
            next_dt = pd.to_datetime(future_perf['start_time'].iloc[0]).astimezone(paris_tz)
            next_time = next_dt.strftime("%H:%M")
        else:
            next_time = "Terminé"
        
        # Conversion Heure de Paris pour la liste complète (delta)
        formatted_times = []
        for t in show_perf['start_time']:
            t_paris = pd.to_datetime(t).astimezone(paris_tz)
            formatted_times.append(t_paris.strftime("%H:%M"))
            
        all_times = ", ".join(formatted_times)

        with cols[i % 3]:
            st.metric(
                label=name,
                value=next_time,
                delta=f"Séances : {all_times}",
                delta_color="off"
            )

with tab_show1: render_shows("DLP")
with tab_show2: render_shows("DAW")

st.divider()

# --- 4. FLUX D'ACTIVITÉS ---
st.header("🚨 Flux d'Activités")
recent_logs = get_recent_logs(supabase, limit=8)
if recent_logs:
    for log in recent_logs:
        time_str = pd.to_datetime(log['start_time']).strftime("%H:%M")
        if log['end_time'] is None:
            render_activity_item(time_str, "⚠️ Interruption", log['ride_name'], cfg.STYLES["orange"])
        else:
            render_activity_item(time_str, "✅ Réouverture", log['ride_name'], cfg.STYLES["green"])
else:
    st.write("Aucun incident récent à signaler.")

st.divider()

# --- 5. ANALYSE DE PERFORMANCE ---
st.header("📊 Analyse de Performance")

col_scope, col_target = st.columns(2)

with col_scope:
    scope = st.selectbox(
        "Niveau d'analyse", 
        ["Global (2 Parcs)", "Par Parc", "Par Land", "Par Attraction"]
    )

target_options = []
if scope == "Par Parc": target_options = ["DLP", "DAW"]
elif scope == "Par Land":
    target_options = list(cfg.PARKS_DATA["Disneyland Park"].keys()) + list(cfg.PARKS_DATA["Disney Adventure World"].keys())
elif scope == "Par Attraction": target_options = cfg.ALL_RIDES_LIST

with col_target:
    target_selection = st.selectbox(f"Choisir la cible", target_options) if target_options else None

# Récupération de la liste des attractions filtrées
rides_to_analyze = []
if scope == "Global (2 Parcs)":
    rides_to_analyze = cfg.ALL_RIDES_LIST
elif scope == "Par Attraction":
    rides_to_analyze = [target_selection] if target_selection else []
else:
    rides_to_analyze = cfg.get_rides_by_zone(target_selection, cfg.ALL_RIDES_LIST)

# Statistiques agrégées
if rides_to_analyze:
    stats = get_stats_for_rides(supabase, rides_to_analyze)
    
    m_cols = st.columns(3)
    m_cols[0].metric("Total Interruptions", stats['total_101'])
    m_cols[1].metric("Moyenne Durée Panne", f"{stats['avg_duration']} min")
    m_cols[2].metric("Attente Moyenne", f"{stats['avg_wait']} min")

    # Graphique d'évolution (Simulé ici, nécessite une table historique pour être réel)
    st.subheader(f"Activité : {target_selection if target_selection else 'Global'}")
    dummy_data = pd.DataFrame([2, 5, 1, 4, 3, 6, 2], columns=["Pannes"])
    st.area_chart(dummy_data, height=180, color="#5072ff")
else:
    st.warning("Sélectionnez une zone pour analyser les données historiques.")