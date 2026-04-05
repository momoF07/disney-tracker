import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime, timedelta
import pytz
import requests
import time
from streamlit_autorefresh import st_autorefresh 
from emojis import get_emoji, get_rides_by_zone
from config import PARK_OPENING, PARK_CLOSING

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Disney Wait Time", page_icon="🏰", layout="centered")

# --- STYLE CSS ---
st.markdown("""
<style>
    [data-testid="stPopoverBody"] {
        position: fixed !important;
        top: 50% !important;
        left: 50% !important;
        transform: translate(-50%, -50%) !important;
        width: 90vw !important;
        max-width: 800px !important;
        max-height: 80vh !important;
        overflow-y: auto !important;
        background-color: rgba(28, 31, 46, 0.98) !important;
        backdrop-filter: blur(20px) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 24px !important;
        padding: 25px !important;
        z-index: 999999 !important;
        box-shadow: 0 20px 40px rgba(0,0,0,0.5) !important;
    }
    code { color: #ff9a9e !important; background: rgba(255,154,158,0.1) !important; }
    [data-testid='stMetricValue'] { font-size: 1.8rem; }
    .stButton button { width: 100%; border-radius: 12px; }
</style>
""", unsafe_allow_html=True)

# --- INITIALISATION ---
paris_tz = pytz.timezone('Europe/Paris')

if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = datetime.now(paris_tz).strftime("%H:%M:%S")

refresh_count = st_autorefresh(interval=60000, key="datarefresh")

if refresh_count > 0:
    st.session_state.last_refresh = datetime.now(paris_tz).strftime("%H:%M:%S")

supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def is_park_theoretically_open(current, opening, closing):
    if opening <= closing: return opening <= current <= closing
    return current >= opening or current <= closing

def trigger_github_action():
    REPO, WORKFLOW_ID, TOKEN = "momoF07/disney-tracker", "check.yml", st.secrets["GITHUB_TOKEN"]
    url = f"https://api.github.com/repos/{REPO}/actions/workflows/{WORKFLOW_ID}/dispatches"
    headers = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        res = requests.post(url, headers=headers, json={"ref": "main"})
        return res.status_code
    except: return 500

# --- LOGIQUE DE TEMPS & RÉCUPÉRATION (Déplacé ici pour éviter NameError) ---
st.title("🏰 Disney Wait Time")
maintenant = datetime.now(paris_tz)
heure_actuelle = maintenant.time()

heure_reset = maintenant.replace(hour=2, minute=30, second=0, microsecond=0)
debut_journee = heure_reset if maintenant >= heure_reset else heure_reset - timedelta(days=1)

# Initialisation par défaut
derniere_maj = "--:--:--"
df_live = pd.DataFrame()
df_pannes = pd.DataFrame()
status_map = {}
all_pannes = []

try:
    resp_live = supabase.table("disney_live").select("*").execute()
    df_live = pd.DataFrame(resp_live.data)
    
    resp_101 = supabase.table("logs_101").select("*").gte("start_time", debut_journee.isoformat()).execute()
    df_pannes = pd.DataFrame(resp_101.data)

    resp_status = supabase.table("daily_status").select("*").execute()
    status_map = {item['ride_name']: item['has_opened_today'] for item in resp_status.data} if resp_status.data else {}

    if not df_live.empty:
        df_live['updated_at'] = pd.to_datetime(df_live['updated_at']).dt.tz_convert('Europe/Paris')
        derniere_maj = df_live['updated_at'].max().strftime("%H:%M:%S")
except Exception as e:
    st.error(f"Erreur Supabase : {e}")

# --- SECTION ACTIONS & STATUS ---
with st.container(border=True):
    c1, c2 = st.columns([1, 1], gap="medium")
    with c1:
        st.markdown("**🔄 Interface**")
        if st.button('Rafraîchir la page', use_container_width=True):
            st.rerun()
    with c2:
        st.markdown("**🤖 Pilotage Robot**")
        btn_robot = st.button('Lancer un relevé 🚀', use_container_width=True, type="primary")
        if btn_robot:
            status_code = trigger_github_action()
            if status_code == 204:
                with st.spinner("Le robot Disney est en route..."):
                    st.toast("✅ Requête acceptée par GitHub !")
                    time.sleep(30)
                    st.rerun()
            else:
                st.error("Échec de connexion")

st.caption(f"🕒 Dernière donnée : **{derniere_maj}** | Prochain relevé auto dans ~60s")

# --- TRAITEMENT DES PANNES ---
if not df_live.empty:
    if not df_pannes.empty:
        for _, row in df_pannes.iterrows():
            d = pd.to_datetime(row['start_time']).astimezone(paris_tz)
            f = pd.to_datetime(row['end_time']).astimezone(paris_tz) if pd.notna(row['end_time']) else None
            all_pannes.append({
                "ride": row['ride_name'], "debut": d, "fin": f,
                "duree": int((f - d).total_seconds() / 60) if f else 0,
                "statut": "EN_COURS" if f is None else "TERMINEE"
            })

    # --- FILTRES ET POPOVER ---
    st.write("---")
    col_sc, col_help = st.columns([0.85, 0.15])
    
    with col_help:
        with st.popover("❓"):
            st.markdown("""
            <style>
                .main-title { text-align: center; background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800; font-size: 28px; margin-bottom: 25px; }
                .cat-badge { padding: 5px 15px; border-radius: 12px; font-size: 18px; font-weight: 600; letter-spacing: 1px; display: block; text-align: center; margin: 20px 0 10px 0; }
                .bg-blue { background: rgba(79, 172, 254, 0.15); color: #4facfe; border: 1px solid rgba(79, 172, 254, 0.3); }
                .bg-green { background: rgba(74, 222, 128, 0.15); color: #4ade80; border: 1px solid rgba(74, 222, 128, 0.3); }
                .bg-orange { background: rgba(251, 191, 36, 0.15); color: #fbbf24; border: 1px solid rgba(251, 191, 36, 0.3); }
                .shortcut-box { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 12px; padding: 10px; margin-bottom: 8px; }
                .shortcut-label { font-size: 15px; color: #94a3b8; text-transform: uppercase; margin-bottom: 5px; display: block; }
            </style>
            """, unsafe_allow_html=True)
            st.markdown('<p class="main-title">🔍 INDEX DES CODES</p>', unsafe_allow_html=True)
            st.markdown('<span class="cat-badge bg-blue">🎡 PARCS</span>', unsafe_allow_html=True)
            with st.container():
                c1, c2, c3 = st.columns(3)
                c1.code("*ALL"); c2.code("*DLP"); c3.code("*DAW")
            st.markdown('<span class="cat-badge bg-green">🏰 DISNEYLAND PARK</span>', unsafe_allow_html=True)
            lands_dlp_map = {"Main Street": ["*MS", "*MAINSTREET"], "Frontierland": ["*FRONTIER", "*FRONTIERLAND"], "Adventureland": ["*ADVENTURE", "*ADVENTURELAND"], "Fantasyland": ["*FANTASY", "*FANTASYLAND"], "Discoveryland": ["*DISCO", "*DISCOVERYLAND"]}
            for land, codes in lands_dlp_map.items():
                st.markdown(f'<div class="shortcut-box"><span class="shortcut-label">{land}</span>', unsafe_allow_html=True)
                cl1, cl2 = st.columns(2); cl1.code(codes[0]); cl2.code(codes[1])
                st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('<span class="cat-badge bg-orange">🎬 ADVENTURE WORLD</span>', unsafe_allow_html=True)
            shortcut_zones_daw = {"Avengers Campus": ["*CAMPUS", "*AVENGERS"], "Production Courtyard": ["*COURTYARD", "*PROD3"], "Worlds of Pixar": ["*PIXAR", "*PROD4"], "World of Frozen": ["*FROZEN", "*WOF"], "Adventure Way": ["*WAY", "*ADVENTURE-WAY"]}
            for zone, codes in shortcut_zones_daw.items():
                st.markdown(f'<div class="shortcut-box"><span class="shortcut-label">{zone}</span>', unsafe_allow_html=True)
                cols_z = st.columns(len(codes))
                for idx, code in enumerate(codes): cols_z[idx].code(code)
                st.markdown('</div>', unsafe_allow_html=True)

    with col_sc:
        sc = st.text_input("Raccourci...", placeholder="ex: *FANTASY", label_visibility="collapsed")
    
    current_selection = st.query_params.get_all("fav")
    if sc.startswith("*"):
        shortcut_selection = get_rides_by_zone(sc, sorted(df_live['ride_name'].unique()), all_pannes)
        if shortcut_selection: current_selection = shortcut_selection

    valid_default = [item for item in current_selection if item in sorted(df_live['ride_name'].unique())]
    selected_options = st.multiselect("Attractions suivies :", options=sorted(df_live['ride_name'].unique()), default=valid_default, format_func=lambda x: f"{get_emoji(x)} {x}")
    st.query_params["fav"] = selected_options
    
    parc_theoriquement_ouvert = is_park_theoretically_open(heure_actuelle, PARK_OPENING, PARK_CLOSING)
    parc_actuellement_ferme = not parc_theoriquement_ouvert
    if parc_actuellement_ferme:
        st.info(f"ℹ️ Le parc est fermé ({PARK_OPENING} -> {PARK_CLOSING}).")

    # --- AFFICHAGE DES ATTRACTIONS ---
    if selected_options:
        st.divider()
        for ride in selected_options:
            ride_data = df_live[df_live['ride_name'] == ride]
            if not ride_data.empty:
                current = ride_data.iloc[0]
                a_deja_ouvert = status_map.get(ride, False)
                panne_actuelle = next((p for p in all_pannes if p['ride'] == ride and p['statut'] == "EN_COURS"), None)
                
                st.subheader(f"{get_emoji(ride)} {ride}")
                c1, c2 = st.columns(2)
                if parc_actuellement_ferme:
                    c1.error("🔴 PARC FERMÉ"); c2.metric("Attente", "- - -")
                elif not a_deja_ouvert:
                    c1.info("🕒 FERMÉ"); c2.metric("Attente", "- - -")
                    st.caption("⏳ En attente de l'ouverture officielle.")
                elif panne_actuelle or not current['is_open']:
                    c1.warning("🔴 INTERRUPTION")
                    if panne_actuelle:
                        delta = maintenant - panne_actuelle['debut']
                        st.caption(f"⚠️ En panne depuis **{max(0, int(delta.total_seconds() / 60))} min** ({panne_actuelle['debut'].strftime('%H:%M')})")
                    c2.metric("Attente", "- - -")
                else:
                    c1.success("🟢 OUVERT"); c2.metric("Attente", f"{int(current['wait_time'])} min")
    
                with st.expander("📜 Historique d'état"):
                    h_pannes = [p for p in all_pannes if p['ride'] == ride]
                    if h_pannes:
                        pannes_triees = sorted(h_pannes, key=lambda x: x['debut'], reverse=True)
                        for idx, p in enumerate(pannes_triees):
                            h_debut = p['debut'].strftime('%H:%M')
                            if idx == 0:
                                if p['statut'] == "EN_COURS": st.write(f"• 🟠 :orange[**En cours** depuis {h_debut}]")
                                else:
                                    st.write(f"• 🟢 :green[**Opérationnel** à {p['fin'].strftime('%H:%M')} ({p['duree']} min)]")
                                    st.caption(f"• 🔴 :red[Panne à {h_debut}]")
                                if len(pannes_triees) > 1: st.markdown("<hr style='margin: -10px 0px 10px 0px; opacity: 0.8;'>", unsafe_allow_html=True)
                            else:
                                with st.container(border=True):
                                    if p['statut'] == "TERMINEE":
                                        st.caption(f"• 🟢 :green[Opérationnel à {p['fin'].strftime('%H:%M')} ({p['duree']} min)]")
                                        st.caption(f"• 🔴 :red[Panne à {h_debut}]")
                    else: st.write("✅ Aucun incident signalé.")
                st.divider()

    st.subheader("🚨 Dernières interruptions")
    if not df_pannes.empty:
        df_pannes['start_time_dt'] = pd.to_datetime(df_pannes['start_time'])
        flux_clean = df_pannes[df_pannes['start_time_dt'] >= debut_journee].sort_values('start_time', ascending=False).head(5)
        for _, p in flux_clean.iterrows():
            d = pd.to_datetime(p['start_time']).astimezone(paris_tz)
            if pd.isna(p['end_time']): st.error(f"🔴 {p['ride_name']} >> depuis {d.strftime('%H:%M')}")
            else:
                f = pd.to_datetime(p['end_time']).astimezone(paris_tz)
                st.success(f"✅ {p['ride_name']} >> fini à {f.strftime('%H:%M')}")

else: 
    st.warning("📭 Aucune donnée live disponible.")
    if "popup_shown" not in st.session_state:
        st.session_state.popup_shown = True

st.divider()
st.caption("Disney Wait Time Tool | Real-time Dashboard")
