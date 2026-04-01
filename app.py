import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime, timedelta, time as dt_time
import pytz
import requests
import time
from streamlit_autorefresh import st_autorefresh 
from emojis import get_emoji, get_rides_by_zone

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
    .shortcut-card {
        background: rgba(255, 255, 255, 0.03);
        border-radius: 12px;
        padding: 10px;
        margin-bottom: 12px;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    .cat-title {
        font-size: 20px;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 8px;
        font-weight: 800;
    }
    .blue-t { color: #4facfe; }
    .green-t { color: #00f2fe; }
    .orange-t { color: #f9d423; }
    
    code {
        color: #ff9a9e !important;
        background: rgba(255,154,158,0.1) !important;
    }
    [data-testid='stMetricValue'] { font-size: 1.8rem; }
    .stButton button { width: 100%; border-radius: 12px; }
</style>
""", unsafe_allow_html=True)

# --- INITIALISATION ---
paris_tz = pytz.timezone('Europe/Paris')
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = datetime.now(paris_tz).strftime("%H:%M:%S")

supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
st_autorefresh(interval=60000, key="datarefresh")
st.session_state.last_refresh = datetime.now(paris_tz).strftime("%H:%M:%S")

def trigger_github_action():
    REPO, WORKFLOW_ID, TOKEN = "momoF07/disney-tracker", "check.yml", st.secrets["GITHUB_TOKEN"]
    url = f"https://api.github.com/repos/{REPO}/actions/workflows/{WORKFLOW_ID}/dispatches"
    headers = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        res = requests.post(url, headers=headers, json={"ref": "main"})
        return res.status_code
    except: return 500

# --- INTERFACE ---
st.title("🏰 Disney Wait Time")
maintenant = datetime.now(paris_tz)

heure_reset = maintenant.replace(hour=2, minute=0, second=0, microsecond=0)
debut_journee = heure_reset - timedelta(days=1) if maintenant < heure_reset else heure_reset

if st.button('🔄 Actualiser & Forcer un Relevé'):
    with st.spinner("Signal envoyé..."):
        if trigger_github_action() == 204:
            st.toast("🚀 Robot lancé !"); time.sleep(45); st.rerun()

# --- RÉCUPÉRATION DES DONNÉES ---
try:
    response = supabase.table("disney_logs")\
        .select("*")\
        .order("created_at", desc=True)\
        .limit(3000)\
        .execute()
    df_raw = pd.DataFrame(response.data)
except Exception as e:
    st.error(f"Erreur Supabase : {e}")
    df_raw = pd.DataFrame()

if not df_raw.empty:
    df_raw['created_at'] = pd.to_datetime(df_raw['created_at'])
    if df_raw['created_at'].dt.tz is None:
        df_raw['created_at'] = df_raw['created_at'].dt.tz_localize('UTC')
    df_raw['created_at'] = df_raw['created_at'].dt.tz_convert('Europe/Paris')
    
    df = df_raw[df_raw['created_at'] >= debut_journee].copy()
    
    if not df.empty:
        derniere_maj = df['created_at'].max().strftime("%H:%M:%S")
        all_pannes = []
        toutes_attractions = sorted(df['ride_name'].unique())
        
        # --- CALCUL DES PANNES ---
        for ride_name in toutes_attractions:
            ride_data = df[df['ride_name'] == ride_name].sort_values('created_at')
            en_panne, debut_panne = False, None
            for i, row in ride_data.iterrows():
                est_nuit_log = (2 <= row['created_at'].hour < 8) and ("Test" not in row['ride_name'])
                if not row['is_open'] and not en_panne and not est_nuit_log:
                    en_panne, debut_panne = True, row['created_at']
                elif row['is_open'] and en_panne:
                    duree = int((row['created_at'] - debut_panne).total_seconds() / 60)
                    all_pannes.append({
                        "ride": ride_name, "debut": debut_panne, "fin": row['created_at'], 
                        "duree": duree, "statut": "TERMINEE"
                    })
                    en_panne = False
            if en_panne:
                all_pannes.append({"ride": ride_name, "debut": debut_panne, "fin": None, "statut": "EN_COURS"})

        # --- LOGIQUE RACCOURCIS & POPOVER ---
        st.write("---")
        col_sc, col_help = st.columns([0.85, 0.15])
        
        with col_help:
            with st.popover("❓"):
                st.markdown("""
                <style>
                    .main-title {
                        text-align: center; 
                        background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%);
                        -webkit-background-clip: text;
                        -webkit-text-fill-color: transparent;
                        font-weight: 800;
                        font-size: 28px;
                        margin-bottom: 25px;
                    }
                    .cat-badge {
                        padding: 5px 15px;
                        border-radius: 12px;
                        font-size: 18px;
                        font-weight: 600;
                        letter-spacing: 1px;
                        display: block;
                        text-align: center;
                        margin: 20px 0 10px 0;
                    }
                    .bg-blue { background: rgba(79, 172, 254, 0.15); color: #4facfe; border: 1px solid rgba(79, 172, 254, 0.3); }
                    .bg-green { background: rgba(74, 222, 128, 0.15); color: #4ade80; border: 1px solid rgba(74, 222, 128, 0.3); }
                    .bg-orange { background: rgba(251, 191, 36, 0.15); color: #fbbf24; border: 1px solid rgba(251, 191, 36, 0.3); }
                    .shortcut-box {
                        background: rgba(255, 255, 255, 0.03);
                        border: 1px solid rgba(255, 255, 255, 0.05);
                        border-radius: 12px;
                        padding: 10px;
                        margin-bottom: 8px;
                    }
                    .shortcut-label {
                        font-size: 15px;
                        color: #94a3b8;
                        text-transform: uppercase;
                        margin-bottom: 5px;
                        display: block;
                    }
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
                    cl1, cl2 = st.columns(2)
                    cl1.code(codes[0]); cl2.code(codes[1])
                    st.markdown('</div>', unsafe_allow_html=True)

                st.markdown('<span class="cat-badge bg-orange">🎬 ADVENTURE WORLD</span>', unsafe_allow_html=True)
                st.markdown('<div class="shortcut-box"><span class="shortcut-label">Avengers Campus</span>', unsafe_allow_html=True)
                ca1, ca2, ca3 = st.columns(3)
                ca1.code("*CAMPUS"); ca2.code("*AVENGERS"); ca3.code("*AVENGERS-CAMPUS")
                st.markdown('</div>', unsafe_allow_html=True)

                st.markdown('<div class="shortcut-box"><span class="shortcut-label">Production Courtyard / Production 3</span>', unsafe_allow_html=True)
                pc1, pc2, pc3 = st.columns(3)
                pc1.code("*COURTYARD"); pc2.code("*PRODUCTION3"); pc3.code("*PROD3")
                st.markdown('</div>', unsafe_allow_html=True)

                st.markdown('<div class="shortcut-box"><span class="shortcut-label">Worlds of Pixar / Production 4</span>', unsafe_allow_html=True)
                cpx1, cpx2, cpx3, cpx4 = st.columns(4)
                cpx1.code("*PIXAR"); cpx2.code("*WORLD-OF-PIXAR"); cpx3.code("*PROD4"); cpx4.code("*PRODUCTION4")
                st.markdown('</div>', unsafe_allow_html=True)

                st.markdown('<div class="shortcut-box"><span class="shortcut-label">World of Frozen</span>', unsafe_allow_html=True)
                cfz1, cfz2, cfz3 = st.columns(3)
                cfz1.code("*WOF"); cfz2.code("*FROZEN"); cfz3.code("*WORLD-OF-FROZEN")
                st.markdown('</div>', unsafe_allow_html=True)

                st.markdown('<div class="shortcut-box"><span class="shortcut-label">Adventure Way</span>', unsafe_allow_html=True)
                aw1, aw2 = st.columns(2)
                aw1.code("*WAY"); aw2.code("*ADVENTURE-WAY")
                st.markdown('</div>', unsafe_allow_html=True)

                st.caption("✨ Astuce : Tapez le code et appuyez sur Entrée.")

        with col_sc:
            sc = st.text_input("Tapez un raccourci...", placeholder="ex: *FANTASY", label_visibility="collapsed")
        
        # --- FILTRAGE AVEC ALL_PANNES POUR *101 / *102 ---
        current_selection = st.query_params.get_all("fav")
        if sc.startswith("*"):
            # IMPORTANT: On passe all_pannes ici
            shortcut_selection = get_rides_by_zone(sc, toutes_attractions, all_pannes)
            if shortcut_selection: current_selection = shortcut_selection

        valid_default = [item for item in current_selection if item in toutes_attractions]
        selected_options = st.multiselect("Attractions suivies :", options=toutes_attractions, default=valid_default, format_func=lambda x: f"{get_emoji(x)} {x}")
        st.query_params["fav"] = selected_options
        
        st.caption(f"🕒 Donnée : {derniere_maj} | Auto-Refresh : {st.session_state.last_refresh} (ne fonctionne pas sur mobile)")
        st.caption("La base de données est vidée tout les soirs à 2h du matin.")
        
        # --- AFFICHAGE DES ATTRACTIONS ---
        est_nuit_actuellement = 2 <= maintenant.hour < 8

        if selected_options:
            st.divider()
            for ride in selected_options:
                ride_df = df[df['ride_name'] == ride].sort_values('created_at', ascending=False)
                if not ride_df.empty:
                    last = ride_df.iloc[0]
                    st.subheader(f"{get_emoji(ride)} {ride}")
                    c1, c2 = st.columns(2)
                    
                    ride_pannes = [p for p in all_pannes if p['ride'] == ride]
                    panne_actuelle = next((p for p in ride_pannes if p['statut'] == "EN_COURS"), None)

                    if last['is_open']:
                        c1.success("🟢 OUVERT")
                        c2.metric("Attente", f"{int(last['wait_time'])} min")
                    else:
                        if est_nuit_actuellement and "Test" not in ride:
                            c1.error("🔴 FERMÉ")
                            st.caption("ℹ️ Le parc est fermé pour la nuit.")
                        else:
                            c1.warning("🔴 INTERRUPTION / PANNE")
                            if panne_actuelle:
                                minutes_ecoulees = int((maintenant - panne_actuelle['debut']).total_seconds() / 60)
                                st.caption(f"⚠️ En panne depuis **{minutes_ecoulees} min**")
                            else:
                                st.caption("⚠️ Attraction indisponible.")
                        c2.metric("Attente", "- - -")
                    
                    with st.expander("📜 Historique des pannes"):
                        if ride_pannes:
                            for p in reversed(ride_pannes):
                                if p['statut'] == "TERMINEE":
                                    st.write(f"• De {p['debut'].strftime('%H:%M')} à {p['fin'].strftime('%H:%M')} (**{p['duree']} min**)")
                                else:
                                    min_inc = int((maintenant - p['debut']).total_seconds() / 60)
                                    st.write(f"• ⚠️ **En cours** depuis {p['debut'].strftime('%H:%M')} ({min_inc} min)")
                        else: st.write("✅ Pas de panne détectée pour le moment.")
                    st.divider()

        # --- FLUX DES PANNES ---
        st.subheader("🚨 Dernières interruptions")
        flux = sorted(all_pannes, key=lambda x: x['debut'], reverse=True)[:5]
        if flux:
            for p in flux:
                if p['statut'] == "EN_COURS": 
                    st.error(f"🔴 {p['ride']}\u00A0\u00A0\u00A0>>\u00A0\u00A0\u00A0{p['debut'].strftime('%H:%M')}")
                else: 
                    st.success(f"✅ {p['ride']}\u00A0\u00A0\u00A0>>\u00A0\u00A0\u00A0{p['fin'].strftime('%H:%M')} -- ({p['duree']} min)")
        else:
            st.write("✅ Aucune interruption en cours.")
    else: st.warning("😴 Maintenance nocturne (02:00 - 08:00).")
else: st.warning("📭 Aucune donnée disponible.")


# --- NOUVEL ONGLET : MON PLANNING ---
st.divider()
with st.expander("📅 Importer mon Planning MyKronos"):
    json_input = st.text_area("Colle le contenu de 'events' ici (JSON)", height=150)
    if st.button("Enregistrer mon planning"):
        if json_input:
            try:
                from ukg_parser import parse_kronos_schedule
                shifts = parse_kronos_schedule(json_input)
                
                # Envoi vers Supabase
                for s in shifts:
                    supabase.table("my_schedule").upsert(s).execute()
                
                st.success(f"✅ {len(shifts)} shifts enregistrés ou mis à jour !")
                time.sleep(2)
                st.rerun()
            except Exception as e:
                st.error(f"Erreur de lecture : {e}")

# --- AFFICHAGE DU PLANNING DU JOUR ---
# On récupère le shift d'aujourd'hui
today_str = maintenant.strftime("%Y-%m-%d")
my_shift = supabase.table("my_schedule").select("*").eq("date", today_str).execute()

if my_shift.data:
    shift = my_shift.data[0]
    st.info(f"📅 **Aujourd'hui :** {shift['location']} | 🕒 {shift['start_time'][11:16]} - {shift['end_time'][11:16]}")
