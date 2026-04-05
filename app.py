import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime, timedelta, time
import pytz
import requests
import time as time_sleep
from streamlit_autorefresh import st_autorefresh 
from emojis import get_emoji, get_rides_by_zone, RIDES_DLP, RIDES_DAW
from config import PARK_OPENING, DLP_CLOSING, DAW_CLOSING
from special_hours import ANTICIPATED_CLOSINGS, FANTASYLAND_EARLY_CLOSE

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

def trigger_github_action():
    REPO, WORKFLOW_ID, TOKEN = "momoF07/disney-tracker", "check.yml", st.secrets["GITHUB_TOKEN"]
    url = f"https://api.github.com/repos/{REPO}/actions/workflows/{WORKFLOW_ID}/dispatches"
    headers = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        res = requests.post(url, headers=headers, json={"ref": "main"})
        return res.status_code
    except: return 500

# --- LOGIQUE DE TEMPS & RÉCUPÉRATION ---
st.title("🏰 Disney Wait Time")
maintenant = datetime.now(paris_tz)
heure_actuelle = maintenant.time()

heure_reset = maintenant.replace(hour=2, minute=30, second=0, microsecond=0)
debut_journee = heure_reset if maintenant >= heure_reset else heure_reset - timedelta(days=1)

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

# --- TRAITEMENT DES PANNES (AVEC FILTRE FIN DE JOURNÉE) ---
if not df_live.empty:
    if not df_pannes.empty:
        for _, row in df_pannes.iterrows():
            ride_n = row['ride_name']
            d_utc = pd.to_datetime(row['start_time'])
            d_paris = d_utc.astimezone(paris_tz)
            f_paris = pd.to_datetime(row['end_time']).astimezone(paris_tz) if pd.notna(row['end_time']) else None
            
            # --- CALCUL DE L'HEURE DE FERMETURE POUR LE FILTRE ---
            is_daw = any(attr.lower() in ride_n.lower() for attr in RIDES_DAW)
            h_ferme = DAW_CLOSING if is_daw else DLP_CLOSING
            if ride_n in ANTICIPATED_CLOSINGS:
                h_ferme = ANTICIPATED_CLOSINGS[ride_n]
            elif ride_n in FANTASYLAND_EARLY_CLOSE:
                full_dt = datetime.combine(datetime.today(), DLP_CLOSING)
                h_ferme = (full_dt - timedelta(minutes=65)).time()
            
            # Seuil de tolérance : 30 minutes avant la fermeture
            dt_ferme = datetime.combine(datetime.today(), h_ferme)
            h_seuil = (dt_ferme - timedelta(minutes=30)).time()
            
            # RÈGLE : Si la panne commence dans les 30 min avant ou après, on l'oublie
            if d_paris.time() >= h_seuil:
                continue
                
            all_pannes.append({
                "ride": ride_n, "debut": d_paris, "fin": f_paris,
                "duree": int((f_paris - d_paris).total_seconds() / 60) if f_paris else 0,
                "statut": "EN_COURS" if f_paris is None else "TERMINEE"
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
            lands_dlp_map = {
                "Main Street": ["*MS", "*MAINSTREET"], 
                "Frontierland": ["*FRONTIER", "*FRONTIERLAND"], 
                "Adventureland": ["*ADVENTURE", "*ADVENTURELAND"], 
                "Fantasyland": ["*FANTASY", "*FANTASYLAND"], 
                "Discoveryland": ["*DISCO", "*DISCOVERYLAND"]
            }
            
            for land, codes in lands_dlp_map.items():
                st.markdown(f'<div class="shortcut-box"><span class="shortcut-label">{land}</span>', unsafe_allow_html=True)
                cl1, cl2 = st.columns(2); cl1.code(codes[0]); cl2.code(codes[1])
                st.markdown('</div>', unsafe_allow_html=True)
                
            st.markdown('<span class="cat-badge bg-orange">🎬 ADVENTURE WORLD</span>', unsafe_allow_html=True)
            shortcut_zones_daw = {
                "Avengers Campus": ["*CAMPUS", "*AVENGERS", "*AVENGERS-CAMPUS"], 
                "Production Courtyard": ["*COURTYARD", "PRODUCTION3", "*PROD3"], 
                "Worlds of Pixar": ["*WORLD-OF-PIXAR", "*PIXAR", "PRODUCTION4", "*PROD4"], 
                "World of Frozen": ["*WORLD-OF-FROZEN", "*FROZEN", "*WOF"], 
                "Adventure Way": ["*WAY", "*ADVENTURE-WAY"]
            }
            
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
    
    # --- AFFICHAGE DES ATTRACTIONS ---
    if selected_options:
        st.divider()
        for ride in selected_options:
            ride_data = df_live[df_live['ride_name'] == ride]
            if not ride_data.empty:
                current = ride_data.iloc[0]
                a_deja_ouvert = status_map.get(ride, False)
                panne_actuelle = next((p for p in all_pannes if p['ride'] == ride and p['statut'] == "EN_COURS"), None)
                
                # --- 1. CALCUL DE L'HEURE DE FERMETURE THÉORIQUE ---
                is_daw_ride = any(attr.lower() in ride.lower() for attr in RIDES_DAW)
                heure_fermeture_theorique = DAW_CLOSING if is_daw_ride else DLP_CLOSING
                
                if ride in ANTICIPATED_CLOSINGS:
                    heure_fermeture_theorique = ANTICIPATED_CLOSINGS[ride]
                elif ride in FANTASYLAND_EARLY_CLOSE:
                    full_dt = datetime.combine(datetime.today(), DLP_CLOSING)
                    heure_fermeture_theorique = (full_dt - timedelta(minutes=65)).time()

                # --- 2. DÉTERMINATION DE L'ÉTAT (AVEC TOLÉRANCE 30MIN) ---
                is_currently_open = current['is_open']
                full_dt_ferme = datetime.combine(datetime.today(), heure_fermeture_theorique)
                heure_tolerance_panne = (full_dt_ferme - timedelta(minutes=30)).time()

                est_apres_heure_limite = heure_actuelle >= heure_fermeture_theorique
                est_dans_zone_ferme = heure_actuelle >= heure_tolerance_panne
                
                # RÈGLE : Fermé déf. si (Zone 30min OU après heure limite) ET is_open=False
                est_definitivement_ferme = (est_dans_zone_ferme or est_apres_heure_limite) and not is_currently_open
                est_en_interruption = not est_dans_zone_ferme and not is_currently_open
                
                if heure_actuelle < PARK_OPENING or heure_actuelle >= DLP_CLOSING:
                    est_definitivement_ferme = True

                st.subheader(f"{get_emoji(ride)} {ride}")
                c1, c2 = st.columns(2)
                
                with c1:
                    if est_definitivement_ferme:
                        st.markdown(f'<div style="display: flex; align-items: center; background-color: rgba(255, 75, 75, 0.1); padding: 10px; border-radius: 12px; border: 2.5px solid rgba(255, 75, 75, 0.5); margin-bottom: 8px;"><span style="color: #ff4b4b; font-weight: 600; font-size: 15px; letter-spacing: 0.3px;">🔴 FERMÉ POUR LA JOURNÉE ({heure_fermeture_theorique.strftime("%H:%M")})</span></div>', unsafe_allow_html=True)
                        c2.metric("Attente", "- - -")
                    elif not a_deja_ouvert:
                        st.markdown('<div style="display: flex; align-items: center; background-color: rgba(0, 123, 255, 0.1); padding: 10px; border-radius: 12px; border: 2.5px solid rgba(0, 123, 255, 0.5); margin-bottom: 8px;"><span style="color: #007bff; font-weight: 600; font-size: 15px; letter-spacing: 0.3px;">🕒 FERMÉ (PAS ENCORE OUVERT)</span></div>', unsafe_allow_html=True)
                        c2.metric("Attente", "- - -")
                    elif est_en_interruption:
                        st.markdown('<div style="display: flex; align-items: center; background-color: rgba(255, 165, 0, 0.1); padding: 10px; border-radius: 12px; border: 2.5px solid rgba(255, 165, 0, 0.5); margin-bottom: 8px;"><div class="mini-loader" style="border: 2px solid rgba(255, 165, 0, 0.2); border-top: 2px solid #FF8C00; border-radius: 50%; width: 16px; height: 16px; animation: spin 1s linear infinite; margin-right: 12px; flex-shrink: 0;"></div><span style="color: #FF8C00; font-weight: 600; font-size: 15px; letter-spacing: 0.3px;">🟠 INTERRUPTION</span></div>', unsafe_allow_html=True)
                        if panne_actuelle:
                            delta = maintenant - panne_actuelle['debut']
                            st.caption(f"⚠️ Depuis {max(0, int(delta.total_seconds() / 60))} min")
                        c2.metric("Attente", "- - -")
                    else:
                        st.markdown('<div style="display: flex; align-items: center; background-color: rgba(46, 204, 113, 0.1); padding: 10px; border-radius: 12px; border: 2.5px solid rgba(46, 204, 113, 0.5); margin-bottom: 8px;"><span style="color: #2ecc71; font-weight: 600; font-size: 15px; letter-spacing: 0.3px;">🟢 OUVERT</span></div>', unsafe_allow_html=True)
                        c2.metric("Attente", f"{int(current['wait_time'])} min")
    
                with st.expander("📜 Historique d'état"):
                    h_pannes = [p for p in all_pannes if p['ride'] == ride]
                    if h_pannes:
                        pannes_triees = sorted(h_pannes, key=lambda x: x['debut'], reverse=True)
                        if est_definitivement_ferme:
                            last_p = pannes_triees[0]
                            if last_p['statut'] == "EN_COURS":
                                st.write(f"• 🔴 :red[**Fermeture à {heure_fermeture_theorique.strftime('%H:%M')}**]")
                                st.caption(f"• 🟠 Panne non résolue (débutée à {last_p['debut'].strftime('%H:%M')})")
                            else:
                                st.write(f"• 🟢 :green[**Opérationnel** jusqu'à la fermeture]")
                                st.caption(f"• ✅ Dernier cycle à {last_p['fin'].strftime('%H:%M')}")
                        else:
                            for idx, p in enumerate(pannes_triees):
                                if idx == 0 and p['statut'] == "EN_COURS":
                                    st.write(f"• 🟠 :orange[**En cours** depuis {p['debut'].strftime('%H:%M')}]")
                                elif p['statut'] == "TERMINEE":
                                    st.write(f"• 🟢 :green[**Opérationnel** à {p['fin'].strftime('%H:%M')} ({p['duree']} min)]")
                                    st.caption(f"• 🔴 :red[Panne à {p['debut'].strftime('%H:%M')}]")
                    else:
                        if est_definitivement_ferme:
                            st.write(f"• 🔴 :red[**Fermeture à {heure_fermeture_theorique.strftime('%H:%M')}**]")
                        else:
                            st.write("✅ Aucun incident signalé.")
                st.divider()

# (Reste du code Dernières interruptions inchangé...)
