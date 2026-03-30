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
st.set_page_config(page_title="Disney Live Control", page_icon="🏰", layout="centered")

# --- CONNEXION SUPABASE ---
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

# --- ACTUALISATION AUTOMATIQUE (60 secondes) ---
st_autorefresh(interval=60000, key="datarefresh")

# --- FONCTION POUR GITHUB ---
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

if st.button('🔄 Actualiser & Forcer un Relevé'):
    with st.spinner("Signal envoyé au robot..."):
        status = trigger_github_action()
        if status == 204:
            st.toast("🚀 Robot lancé !", icon="✅")
            time.sleep(40) 
            st.rerun()

# --- RÉCUPÉRATION DES DONNÉES (24h) ---
try:
    hier = maintenant - timedelta(hours=24)
    response = supabase.table("disney_logs") \
        .select("*") \
        .gte("created_at", hier.isoformat()) \
        .order("created_at", desc=False) \
        .execute()
    df = pd.DataFrame(response.data)
except:
    df = pd.DataFrame()

if not df.empty:
    df['created_at'] = pd.to_datetime(df['created_at']).dt.tz_convert('Europe/Paris')
    derniere_maj = df['created_at'].max().strftime("%H:%M:%S")

    # --- CALCUL GLOBAL DES PANNES (Pour usage plus bas) ---
    all_pannes = []
    for ride_name in df['ride_name'].unique():
        ride_data = df[df['ride_name'] == ride_name].sort_values('created_at')
        en_panne = False
        debut_panne = None
        for i, row in ride_data.iterrows():
            if not row['is_open'] and not en_panne:
                en_panne = True
                debut_panne = row['created_at']
            elif row['is_open'] and en_panne:
                fin_panne = row['created_at']
                all_pannes.append({
                    "ride": ride_name, "debut": debut_panne, "fin": fin_panne,
                    "duree": int((fin_panne - debut_panne).total_seconds() / 60),
                    "statut": "TERMINEE"
                })
                en_panne = False
        if en_panne:
            all_pannes.append({"ride": ride_name, "debut": debut_panne, "fin": None, "statut": "EN_COURS"})

    # --- SECTION FAVORIS ---
    toutes_attractions = sorted(df['ride_name'].unique())
    selected_options = st.multiselect("Favoris :", options=toutes_attractions, default=st.query_params.get_all("fav"), format_func=lambda x: f"{get_emoji(x)} {x}")
    st.query_params["fav"] = selected_options
    
    st.caption(f"🕒 Donnée : {derniere_maj} | Auto-refresh : 60s")
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
                    c1.error("🔴 FERMÉ / PANNE")
                    c2.metric("Attente", "- - -")

                # 1. BLOC JAUNE ALERTE
                ride_pannes = [p for p in all_pannes if p['ride'] == ride]
                panne_actuelle = next((p for p in ride_pannes if p['statut'] == "EN_COURS"), None)
                if panne_actuelle:
                    min_encours = int((maintenant - panne_actuelle['debut']).total_seconds() / 60)
                    st.warning(f"⚠️ En panne depuis {min_encours} min (à {panne_actuelle['debut'].strftime('%H:%M')})")

                # 2. GRAPHIQUE IMMOBILE
                if len(ride_df) > 1 and last['is_open']:
                    four_h = maintenant - timedelta(hours=4)
                    chart_data = ride_df[ride_df['created_at'] >= four_h].copy()
                    gradient = alt.Gradient(
                        gradient='linear',
                        stops=[
                            alt.GradientStop(color='green', offset=0), alt.GradientStop(color='green', offset=25/80),
                            alt.GradientStop(color='orange', offset=35/80), alt.GradientStop(color='orange', offset=55/80),
                            alt.GradientStop(color='red', offset=65/80), alt.GradientStop(color='red', offset=1)
                        ],
                        x1=0, x2=0, y1=1, y2=0 
                    )
                    base = alt.Chart(chart_data).encode(
                        x=alt.X('created_at:T', title=None, axis=alt.Axis(format="%H:%M", grid=False)),
                        y=alt.Y('wait_time:Q', title=None, scale=alt.Scale(domain=[0, 80]), axis=alt.Axis(grid=True))
                    )
                    area = base.mark_area(color=gradient, line={'color': '#1f77b4', 'strokeWidth': 2}, opacity=0.9, interpolate='monotone', tooltip=False)
                    st.altair_chart(area.properties(height=200).interactive(False), use_container_width=True, theme=None)

                # 3. HISTORIQUE LOCAL
                if ride_pannes:
                    with st.expander("📜 Historique des pannes"):
                        for p in reversed(ride_pannes):
                            if p['statut'] == "TERMINEE":
                                st.write(f"• Panne de {p['debut'].strftime('%H:%M')} à {p['fin'].strftime('%H:%M')} ({p['duree']} min)")
                            else:
                                diff_encours = int((maintenant - p['debut']).total_seconds() / 60)
                                st.write(f"• ⚠️ **En cours** : depuis {p['debut'].strftime('%H:%M')} ({diff_encours} min)")
                st.divider()

    # --- SECTION : FLUX DES DERNIÈRES PANNES (EN BAS) ---
    st.subheader("🚨 Flux des dernières pannes du parc")
    flux_pannes = sorted(all_pannes, key=lambda x: x['debut'], reverse=True)[:5]
    if flux_pannes:
        for p in flux_pannes:
            if p['statut'] == "EN_COURS":
                st.error(f"🔴 **{p['ride']}** est tombé en panne à {p['debut'].strftime('%H:%M')}")
            else:
                st.info(f"✅ **{p['ride']}** a rouvert à {p['fin'].strftime('%H:%M')} ({p['duree']} min)")
    else:
        st.write("✅ Aucune panne enregistrée.")

else:
    st.warning("📭 Aucune donnée disponible.")

st.markdown("""
    <style>
    [data-testid='stMetricValue'] { font-size: 1.8rem; } 
    .stButton button { width: 100%; border-radius: 10px; }
    details { display: none !important; }
    </style>
    """, unsafe_allow_html=True)
