# frontierland_app.py
import streamlit as st
from supabase import create_client
import os
import pandas as pd
from datetime import datetime
import pytz

st.set_page_config(page_title="Frontierland Live", layout="wide", initial_sidebar_context="collapsed")

url = os.environ.get("SUPABASE_URL") or st.secrets.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY") or st.secrets.get("SUPABASE_KEY")
supabase = create_client(url, key)

paris_tz = pytz.timezone('Europe/Paris')

FRONTIERLAND_RIDES = {
    "Big Thunder Mountain":           "⛰️",
    "Phantom Manor":                  "👻",
    "Thunder Mesa Riverboat Landing": "🚢",
    "Disneyland Railroad":            "🚂",
    "Frontierland Playground":        "🌵",
}

RAILROAD_RIDES = [
    "Disneyland Railroad Main Street Station",
    "Disneyland Railroad Frontierland Depot",
]

COLOR  = "#ef6c00"
COLOR_L = "#fb923c"

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Barlow:wght@300;400;500;600;700&display=swap');

    * {{ box-sizing: border-box; margin: 0; padding: 0; }}

    .stApp {{
        background:
            radial-gradient(ellipse 120% 60% at 10% 0%, rgba(239,108,0,0.12) 0%, transparent 55%),
            radial-gradient(ellipse 80% 60% at 90% 100%, rgba(251,146,60,0.08) 0%, transparent 55%),
            #08090d;
        font-family: 'Barlow', sans-serif;
    }}

    .block-container {{
        padding: 2rem 1.5rem !important;
        max-width: 100% !important;
    }}

    .page-title {{
        font-family: 'Bebas Neue', sans-serif;
        font-size: 3.5rem;
        letter-spacing: 4px;
        color: {COLOR};
        text-align: center;
        margin-bottom: 0.2rem;
        text-shadow: 0 0 40px {COLOR}44;
    }}

    .page-sub {{
        text-align: center;
        color: rgba(255,255,255,0.25);
        font-size: 11px;
        font-weight: 500;
        letter-spacing: 3px;
        text-transform: uppercase;
        margin-bottom: 2.5rem;
    }}

    .ride-card {{
        background: rgba(255,255,255,0.025);
        border: 1px solid rgba(239,108,0,0.15);
        border-radius: 20px;
        padding: 24px 16px 20px;
        height: 100%;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 14px;
        position: relative;
        overflow: hidden;
    }}

    .ride-card::before {{
        content: '';
        position: absolute;
        bottom: 0; left: 0; right: 0;
        height: 3px;
        background: linear-gradient(90deg, transparent, {COLOR}, transparent);
        opacity: 0.6;
    }}

    .ride-emoji {{
        font-size: 52px;
        line-height: 1;
        filter: drop-shadow(0 0 20px {COLOR}66);
    }}

    .ride-name {{
        font-family: 'Bebas Neue', sans-serif;
        font-size: 1.1rem;
        letter-spacing: 2px;
        color: rgba(255,255,255,0.85);
        text-align: center;
        line-height: 1.2;
    }}

    .wait-block {{
        display: flex;
        flex-direction: column;
        align-items: center;
        background: {COLOR}18;
        border: 1px solid {COLOR}35;
        border-radius: 14px;
        padding: 10px 20px;
        width: 100%;
    }}

    .wait-val {{
        font-family: 'Bebas Neue', sans-serif;
        font-size: 2.8rem;
        color: {COLOR};
        line-height: 1;
        text-shadow: 0 0 20px {COLOR}66;
    }}

    .wait-label {{
        font-size: 9px;
        color: {COLOR}99;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 2px;
    }}

    .status-pill {{
        font-size: 10px;
        font-weight: 700;
        padding: 3px 12px;
        border-radius: 20px;
        text-transform: uppercase;
        letter-spacing: 1.5px;
    }}

    .divider {{
        width: 100%;
        height: 1px;
        background: rgba(255,255,255,0.05);
    }}

    .stats-row {{
        display: flex;
        gap: 6px;
        flex-wrap: wrap;
        justify-content: center;
        width: 100%;
    }}

    .stat-badge {{
        display: inline-flex;
        flex-direction: column;
        align-items: center;
        background: {COLOR}12;
        border: 1px solid {COLOR}28;
        border-radius: 10px;
        padding: 5px 10px;
        min-width: 48px;
    }}

    .stat-val {{
        font-family: 'Bebas Neue', sans-serif;
        font-size: 1.2rem;
        color: {COLOR};
        line-height: 1;
    }}

    .stat-lbl {{
        font-size: 6.5px;
        color: {COLOR}80;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        margin-top: 2px;
    }}

    .stat-badge-sm {{
        display: inline-flex;
        flex-direction: column;
        align-items: center;
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 8px;
        padding: 3px 8px;
        min-width: 40px;
    }}

    .stat-val-sm {{
        font-family: 'Bebas Neue', sans-serif;
        font-size: 0.9rem;
        color: rgba(255,255,255,0.35);
        line-height: 1;
    }}

    .stat-lbl-sm {{
        font-size: 6px;
        color: rgba(255,255,255,0.2);
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        margin-top: 1px;
    }}

    .prev-label {{
        font-size: 7.5px;
        color: rgba(255,255,255,0.2);
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        text-align: center;
        width: 100%;
    }}
</style>
""", unsafe_allow_html=True)

# ============================================================
# DONNÉES
# ============================================================
now_paris     = datetime.now(paris_tz)
debut_mois    = now_paris.replace(day=1, hour=2, minute=30, second=0, microsecond=0)
debut_mois_pr = (debut_mois - pd.DateOffset(months=1)).to_pydatetime()

MOIS_FR = {1:"Jan",2:"Fév",3:"Mar",4:"Avr",5:"Mai",6:"Jun",
           7:"Jul",8:"Aoû",9:"Sep",10:"Oct",11:"Nov",12:"Déc"}
mois_label    = f"{MOIS_FR[now_paris.month]} {now_paris.year}"
mois_pr_label = f"{MOIS_FR[debut_mois_pr.month]} {debut_mois_pr.year}"

@st.cache_data(ttl=60)
def load_data():
    live   = {r['ride_name']: r for r in supabase.table("disney_live").select("*").execute().data}
    status = {r['ride_name']: r for r in supabase.table("daily_status").select("*").execute().data}

    def get_logs(date_from, date_to=None):
        q = supabase.table("logs_101").select("*").gte("start_time", date_from.isoformat())
        if date_to:
            q = q.lt("start_time", date_to.isoformat())
        df = pd.DataFrame(q.execute().data)
        if df.empty: return df
        df['start_dt']  = pd.to_datetime(df['start_time'], format='mixed').dt.tz_convert('Europe/Paris')
        df['end_dt']    = df['end_time'].apply(
            lambda x: pd.to_datetime(x, format='mixed').tz_convert('Europe/Paris') if pd.notna(x)
            else pd.Timestamp.now(tz='Europe/Paris')
        )
        df['duree_min'] = (df['end_dt'] - df['start_dt']).dt.total_seconds() / 60
        df = df[(df['duree_min'] >= 5) & (df['duree_min'] <= 420)]
        return df

    logs_mois    = get_logs(debut_mois)
    logs_mois_pr = get_logs(debut_mois_pr, debut_mois)
    return live, status, logs_mois, logs_mois_pr

live, status, logs_mois, logs_mois_pr = load_data()

# ============================================================
# HEADER
# ============================================================
st.markdown('<div class="page-title">🌵 Frontierland Live</div>', unsafe_allow_html=True)
st.markdown(f'<div class="page-sub">Temps réel · {now_paris.strftime("%H:%M:%S")} · {mois_label}</div>', unsafe_allow_html=True)

# ============================================================
# CARTES
# ============================================================
cols = st.columns(len(FRONTIERLAND_RIDES), gap="medium")

for col, (ride_name, emoji) in zip(cols, FRONTIERLAND_RIDES.items()):
    with col:
        # Données live
        if ride_name == "Disneyland Railroad":
            ride_data = (live.get("Disneyland Railroad Main Street Station") or
                         live.get("Disneyland Railroad Frontierland Depot") or {})
            df_r      = logs_mois[logs_mois['ride_name'].isin(RAILROAD_RIDES)] if not logs_mois.empty else pd.DataFrame()
            df_r_pr   = logs_mois_pr[logs_mois_pr['ride_name'].isin(RAILROAD_RIDES)] if not logs_mois_pr.empty else pd.DataFrame()
        else:
            ride_data = live.get(ride_name, {})
            df_r      = logs_mois[logs_mois['ride_name'] == ride_name] if not logs_mois.empty else pd.DataFrame()
            df_r_pr   = logs_mois_pr[logs_mois_pr['ride_name'] == ride_name] if not logs_mois_pr.empty else pd.DataFrame()

        is_open = ride_data.get('is_open', False)
        wait    = ride_data.get('wait_time', 0) or 0

        # Stats
        nb    = len(df_r)
        total = int(df_r['duree_min'].sum()) if nb > 0 else 0
        moy   = int(df_r['duree_min'].mean()) if nb > 0 else 0

        nb_pr    = len(df_r_pr)
        total_pr = int(df_r_pr['duree_min'].sum()) if nb_pr > 0 else 0
        moy_pr   = int(df_r_pr['duree_min'].mean()) if nb_pr > 0 else 0

        # Affichage
        if is_open:
            status_color = "#10b981"
            status_label = "Ouvert"
            wait_display = str(int(wait))
            wait_unit    = "MIN"
        else:
            status_color = "#f59e0b"
            status_label = "Fermé"
            wait_display = "—"
            wait_unit    = "ATTENTE"

        st.markdown(f"""
        <div class="ride-card">
            <div class="ride-emoji">{emoji}</div>
            <div class="ride-name">{ride_name}</div>

            <div class="wait-block">
                <div class="wait-val">{wait_display}</div>
                <div class="wait-label">{wait_unit}</div>
            </div>

            <span class="status-pill" style="background:{status_color}20; color:{status_color}; border:1px solid {status_color}40;">
                {status_label}
            </span>

            <div class="divider"></div>

            <div style="font-size:8px; color:rgba(255,255,255,0.25); font-weight:700;
                        text-transform:uppercase; letter-spacing:1.5px; width:100%; text-align:center;">
                {mois_label}
            </div>
            <div class="stats-row">
                <div class="stat-badge">
                    <div class="stat-val">{nb}</div>
                    <div class="stat-lbl">101</div>
                </div>
                <div class="stat-badge">
                    <div class="stat-val">{total}</div>
                    <div class="stat-lbl">min</div>
                </div>
                <div class="stat-badge">
                    <div class="stat-val">{moy}</div>
                    <div class="stat-lbl">∅ min</div>
                </div>
            </div>

            <div class="divider"></div>

            <div class="prev-label">📅 {mois_pr_label}</div>
            <div class="stats-row">
                <div class="stat-badge-sm">
                    <div class="stat-val-sm">{nb_pr}</div>
                    <div class="stat-lbl-sm">101</div>
                </div>
                <div class="stat-badge-sm">
                    <div class="stat-val-sm">{total_pr}</div>
                    <div class="stat-lbl-sm">min</div>
                </div>
                <div class="stat-badge-sm">
                    <div class="stat-val-sm">{moy_pr}</div>
                    <div class="stat-lbl-sm">∅ min</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

footer_html = f"""
<style>
    .main-footer {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 15px 5px;
        color: #64748b;
        font-family: 'Inter', sans-serif;
        border-top: 1px solid rgba(255, 255, 255, 0.05);
        margin-top: 20px;
    }}
    .footer-item {{
        font-size: 11px;
        letter-spacing: 0.5px;
    }}
    .footer-separator {{
        margin: 0 8px;
        opacity: 0.3;
    }}
    .version-tag {{
        background: rgba(255, 255, 255, 0.05);
        padding: 2px 8px;
        border-radius: 10px;
        font-weight: 700;
        color: #94a3b8;
    }}
</style>

<div class="main-footer">
    <div class="footer-item">
        <span class="version-tag">{webversion}</span>
        <span class="footer-separator">|</span>
        Disney Wait Time Tool
    </div>
    <div class="footer-item" style="text-align: center; flex-grow: 1;">
        API Attente : ThemePark Wiki <span class="footer-separator">•</span> API Météo : Open Meteo
    </div>
    <div class="footer-item" style="text-align: right;">
        Actualisé à : <b>{st.session_state.last_refresh}</b>
    </div>
</div>
"""
st.markdown(footer_html, unsafe_allow_html=True)