import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime, timedelta, time, date
import pytz
import requests
import time as time_sleep
import random
from streamlit_autorefresh import st_autorefresh 
from emojis import get_emoji, get_rides_by_zone, RIDES_DLP, RIDES_DAW
# On importe les nouvelles variables de config
from config import PARK_OPENING, DLP_CLOSING, DAW_CLOSING, EMT_OPENING
# On ajoute EMT_EARLY_OPEN aux imports
from special_hours import ANTICIPATED_CLOSINGS, FANTASYLAND_EARLY_CLOSE, EMT_EARLY_OPEN

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
aujourdhui_date = maintenant.date()
heure_actuelle = maintenant.time()

heure_reset = maintenant.replace(hour=2, minute=30, second=0, microsecond=0)
debut_journee = heure_reset if maintenant >= heure_reset else heure_reset - timedelta(days=1)

derniere_maj = "--:--:--"
df_live = pd.DataFrame()
df_pannes_brutes = pd.DataFrame()
status_map = {}
db_rehabs = {}
all_pannes = []

try:
    resp_live = supabase.table("disney_live").select("*").execute()
    df_live = pd.DataFrame(resp_live.data)
    
    resp_101 = supabase.table("logs_101").select("*").gte("start_time", debut_journee.isoformat()).execute()
    df_pannes_brutes = pd.DataFrame(resp_101.data)

    resp_status = supabase.table("daily_status").select("*").execute()
    status_map = {item['ride_name']: item['has_opened_today'] for item in resp_status.data} if resp_status.data else {}

    # Récupération des maintenances depuis Supabase
    resp_rehabs = supabase.table("ride_schedules").select("*").execute()
    db_rehabs = {item['ride_name']: item for item in resp_rehabs.data} if resp_rehabs.data else {}

    if not df_live.empty:
        df_live['updated_at'] = pd.to_datetime(df_live['updated_at']).dt.tz_convert('Europe/Paris')
        derniere_maj = df_live['updated_at'].max().strftime("%H:%M:%S")
except Exception as e:
    st.error(f"Erreur Supabase : {e}")

# --- TRAITEMENT DES PANNES (FILTRE FIN DE JOURNÉE) ---
if not df_live.empty and not df_pannes_brutes.empty:
    for _, row in df_pannes_brutes.iterrows():
        r_name = row['ride_name']
        d_paris = pd.to_datetime(row['start_time']).astimezone(paris_tz)
        f_paris = pd.to_datetime(row['end_time']).astimezone(paris_tz) if pd.notna(row['end_time']) else None
        
        is_daw = any(attr.lower() in r_name.lower() for attr in RIDES_DAW)
        h_f = DAW_CLOSING if is_daw else DLP_CLOSING
        if r_name in ANTICIPATED_CLOSINGS:
            h_f = ANTICIPATED_CLOSINGS[r_name]
        elif r_name in FANTASYLAND_EARLY_CLOSE:
            h_f = (datetime.combine(datetime.today(), DLP_CLOSING) - timedelta(minutes=65)).time()
        
        h_seuil = (datetime.combine(datetime.today(), h_f) - timedelta(minutes=30)).time()
        
        if d_paris.time() >= h_seuil:
            continue
            
        all_pannes.append({
            "ride": r_name, "debut": d_paris, "fin": f_paris,
            "duree": int((f_paris - d_paris).total_seconds() / 60) if f_paris else 0,
            "statut": "EN_COURS" if f_paris is None else "TERMINEE"
        })

# --- PANEL ADMIN GLOBAL ---
st.sidebar.write("---")
with st.sidebar.expander("🔐 Panel Administration"):
    admin_password = st.text_input("Mot de passe", type="password", key="global_admin_pass")
    
    if admin_password == st.secrets.get("ADMIN_PASSWORD", "disney123"):
        
        # --- ONGLET 1 : SIMULATION DE FLUX ---
        st.markdown("### 🧪 Simulation (Test)")
        sim_mode = st.toggle("Activer Mode Simulation")
        if sim_mode and not df_live.empty:
            st.warning("⚠️ Mode test actif")
            df_live['wait_time'] = [random.randint(0, 12) * 5 for _ in range(len(df_live))]
            for idx, row in df_live.iterrows():
                ride_n = row['ride_name']
                etat_test = random.choice(["OUVERT", "INTERRUPTION", "JAMAIS_OUVERT"])
                if etat_test == "OUVERT":
                    df_live.at[idx, 'is_open'] = True
                    status_map[ride_n] = True
                elif etat_test == "INTERRUPTION":
                    df_live.at[idx, 'is_open'] = False
                    status_map[ride_n] = True 
                    all_pannes.append({"ride": ride_n, "debut": maintenant - timedelta(minutes=15), "fin": None, "statut": "EN_COURS"})
                elif etat_test == "JAMAIS_OUVERT":
                    df_live.at[idx, 'is_open'] = False
                    status_map[ride_n] = False 

        st.markdown("---")

        # --- ONGLET 2 : GESTION DES TRAVAUX (SUPABASE) ---
        st.markdown("### 🛠️ Gestion des Travaux")
        with st.form("rehab_form", clear_on_submit=True):
            if not df_live.empty:
                all_rides_names = sorted(df_live['ride_name'].unique())
                sel_ride = st.selectbox("Attraction", all_rides_names)
            else:
                sel_ride = st.text_input("Nom de l'attraction")
            
            col_d1, col_d2 = st.columns(2)
            d_start = col_d1.date_input("Début", value=date.today())
            d_end = col_d2.date_input("Fin", value=date.today() + timedelta(days=14))
            
            rehab_msg = st.text_input("Message", placeholder="ex: Réouverture le 30 mai")
            is_active = st.checkbox("Activer le badge gris", value=True)
            
            if st.form_submit_button("Enregistrer en Base"):
                try:
                    payload = {
                        "ride_name": sel_ride,
                        "rehab_start": str(d_start),
                        "rehab_end": str(d_end),
                        "rehab_msg": rehab_msg,
                        "is_refurb": is_active,
                        "updated_at": "now()"
                    }
                    supabase.table("ride_schedules").upsert(payload).execute()
                    st.success(f"✅ {sel_ride} enregistré !")
                    time_sleep.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Erreur : {e}")

        # --- LISTE DES TRAVAUX ACTUELS (POUR SUPPRESSION) ---
        st.markdown("#### 📋 Maintenances actives")
        try:
            res_db = supabase.table("ride_schedules").select("*").eq("is_refurb", True).execute()
            if res_db.data:
                for r in res_db.data:
                    c_info, c_del = st.columns([0.8, 0.2])
                    c_info.caption(f"**{r['ride_name']}** (Fin: {r['rehab_end']})")
                    if c_del.button("🗑️", key=f"del_{r['id']}"):
                        supabase.table("ride_schedules").delete().eq("id", r['id']).execute()
                        st.rerun()
            else:
                st.info("Aucun travaux en base.")
        except:
            pass

    elif admin_password != "":
        st.error("Mot de passe incorrect")

# --- SECTION ACTIONS ---
col_btn1, col_btn2 = st.columns(2)
with col_btn1:
    if st.button('🔄 Rafraîchir l\'Affichage'):
        st.rerun()
with col_btn2:
    if st.button('🚀 Forcer un Relevé Manuel', type="primary"):
        status_code = trigger_github_action()
        if status_code == 204:
            with st.status("Le robot Disney récupère les temps...", expanded=False):
                st.toast("✅ Requête acceptée !")
                time_sleep.sleep(40)
                st.rerun()

st.markdown(f"""
    <div style="background-color: rgba(255, 255, 255, 0.05); padding: 10px; border-radius: 10px; border-left: 5px solid #4facfe; margin-bottom: 20px;">
        <span style="font-size: 14px; color: #94a3b8;">🕒 Donnée API : <b>{derniere_maj}</b> | Synchro Refresh : <b>{st.session_state.last_refresh}</b></span>
    </div>
""", unsafe_allow_html=True)

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
    shortcut_selection = get_rides_by_zone(sc, sorted(df_live['ride_name'].unique()) if not df_live.empty else [], all_pannes)
    if shortcut_selection: current_selection = shortcut_selection

if not df_live.empty:
    options_list = sorted(df_live['ride_name'].unique())
    valid_default = [item for item in current_selection if item in options_list]
    selected_options = st.multiselect("Attractions suivies :", options=options_list, default=valid_default, format_func=lambda x: f"{get_emoji(x)} {x}")
    st.query_params["fav"] = selected_options

    if selected_options:
        st.divider()
        for ride in selected_options:
            ride_data = df_live[df_live['ride_name'] == ride]
            if not ride_data.empty:
                current = ride_data.iloc[0]
                a_deja_ouvert = status_map.get(ride, False)
                panne_actuelle = next((p for p in all_pannes if p['ride'] == ride and p['statut'] == "EN_COURS"), None)
                
                heure_fermeture_constatee = current['updated_at'].strftime("%H:%M")
                
                # --- LOGIQUE RÉHABILITATION (TRAVAUX) ---
                infos_rehab = db_rehabs.get(ride)
                est_en_rehab = False
                est_bientot_rehab = False
                
                if infos_rehab and infos_rehab.get('is_refurb'):
                    d_start = datetime.strptime(infos_rehab['rehab_start'], '%Y-%m-%d').date()
                    d_end = datetime.strptime(infos_rehab['rehab_end'], '%Y-%m-%d').date()
                    
                    if d_start <= aujourdhui_date <= d_end:
                        est_en_rehab = True
                    elif 0 < (d_start - aujourdhui_date).days <= 7:
                        est_bientot_rehab = True

                # --- LOGIQUE EMT / OUVERTURE THÉORIQUE ---
                h_ouverture_theorique = EMT_OPENING if ride in EMT_EARLY_OPEN else PARK_OPENING
                
                is_daw_ride = any(attr.lower() in ride.lower() for attr in RIDES_DAW)
                h_f_theorique = DAW_CLOSING if is_daw_ride else DLP_CLOSING
                if ride in ANTICIPATED_CLOSINGS:
                    h_f_theorique = ANTICIPATED_CLOSINGS[ride]
                elif ride in FANTASYLAND_EARLY_CLOSE:
                    h_f_theorique = (datetime.combine(datetime.today(), DLP_CLOSING) - timedelta(minutes=65)).time()

                h_tolerance = (datetime.combine(datetime.today(), h_f_theorique) - timedelta(minutes=30)).time()
                is_open_api = current['is_open']
                
                # --- DÉTERMINATION DES ÉTATS ---
                est_definitivement_ferme = (heure_actuelle >= h_tolerance or heure_actuelle >= h_f_theorique) and not is_open_api
                est_en_attente = heure_actuelle < h_ouverture_theorique and not is_open_api
                est_en_interruption = heure_actuelle >= h_ouverture_theorique and heure_actuelle < h_tolerance and not is_open_api
                
                if (heure_actuelle < h_ouverture_theorique and not is_open_api) and not sim_mode:
                    if heure_actuelle < EMT_OPENING:
                        est_en_attente = True

                st.subheader(f"{get_emoji(ride)} {ride}")
                c1, c2 = st.columns(2)
                
                with c1:
                    # CAS 0 : EN RÉHABILITATION
                    if est_en_rehab:
                        st.markdown(f'<div style="background-color: rgba(128, 128, 128, 0.1); padding: 10px; border-radius: 12px; border: 2.5px solid rgba(128, 128, 128, 0.5); margin-bottom: 8px;"><span style="color: #808080; font-weight: 600; font-size: 15px;">🛠️ EN RÉHABILITATION</span></div>', unsafe_allow_html=True)
                        st.caption(f"⏳ Jusqu'au {datetime.strptime(infos_rehab['rehab_end'], '%Y-%m-%d').strftime('%d/%m')}")
                        c2.metric("Attente", "TRVX")

                    # CAS 1 : Fermé pour la journée
                    elif est_definitivement_ferme:
                        st.markdown(f'<div style="background-color: rgba(255, 75, 75, 0.1); padding: 10px; border-radius: 12px; border: 2.5px solid rgba(255, 75, 75, 0.5); margin-bottom: 8px;"><span style="color: #ff4b4b; font-weight: 600; font-size: 15px;">🔴 FERMÉ DEPUIS {heure_fermeture_constatee}</span></div>', unsafe_allow_html=True)
                        c2.metric("Attente", "- - -")
                    
                    # CAS 2 : En attente
                    elif est_en_attente:
                        st.markdown('<div style="background-color: rgba(0, 123, 255, 0.1); padding: 10px; border-radius: 12px; border: 2.5px solid rgba(0, 123, 255, 0.5); margin-bottom: 8px;"><span style="color: #007bff; font-weight: 600; font-size: 15px;">🕒 EN ATTENTE</span></div>', unsafe_allow_html=True)
                        c2.metric("Attente", "- - -")
                    
                    # CAS 3 : OUVERTURE RETARDÉE
                    elif est_en_interruption and not a_deja_ouvert:
                        st.markdown('<div style="background-color: rgba(155, 89, 182, 0.1); padding: 10px; border-radius: 12px; border: 2.5px solid rgba(155, 89, 182, 0.5); margin-bottom: 8px;"><span style="color: #9b59b6; font-weight: 600; font-size: 15px;">🟣 OUVERTURE RETARDÉE</span></div>', unsafe_allow_html=True)
                        c2.metric("Attente", "- - -")

                    # CAS 4 : INTERRUPTION
                    elif est_en_interruption and a_deja_ouvert:
                        st.markdown('<div style="background-color: rgba(255, 165, 0, 0.1); padding: 10px; border-radius: 12px; border: 2.5px solid rgba(255, 165, 0, 0.5); margin-bottom: 8px;"><span style="color: #FF8C00; font-weight: 600; font-size: 15px;">🟠 INTERRUPTION DE SERVICE</span></div>', unsafe_allow_html=True)
                        if panne_actuelle: st.caption(f"⚠️ Depuis {max(0, int((maintenant - panne_actuelle['debut']).total_seconds() / 60))} min")
                        c2.metric("Attente", "- - -")
                    
                    # CAS 5 : OUVERT
                    else:
                        if est_bientot_rehab:
                             st.caption(f"⚠️ Maintenance le {datetime.strptime(infos_rehab['rehab_start'], '%Y-%m-%d').strftime('%d/%m')}")
                        st.markdown('<div style="background-color: rgba(46, 204, 113, 0.1); padding: 10px; border-radius: 12px; border: 2.5px solid rgba(46, 204, 113, 0.5); margin-bottom: 8px;"><span style="color: #2ecc71; font-weight: 600; font-size: 15px;">🟢 OUVERT</span></div>', unsafe_allow_html=True)
                        c2.metric("Attente", f"{int(current['wait_time'])} min")
                        
                with st.expander("📜 Historique d'état"):
                    if est_en_rehab:
                        st.write(f"• 🛠️ :grey[**Maintenance en cours**]")
                        st.caption(f"• {infos_rehab.get('rehab_msg', 'Travaux de maintenance')}")
                    else:
                        h_pannes_brutes = [p for p in all_pannes if p['ride'] == ride]
                        h_pannes_clean = [p for p in h_pannes_brutes if p['statut'] == "EN_COURS" or p['duree'] >= 3]
                        
                        if h_pannes_clean:
                            pannes_triees = sorted(h_pannes_clean, key=lambda x: x['debut'], reverse=True)
                            for idx, p in enumerate(pannes_triees):
                                h_debut = p['debut'].strftime('%H:%M')
                                if idx == 0:
                                    if est_definitivement_ferme:
                                        st.write(f"• 🔴 :red[**Fermé à {heure_fermeture_constatee}**]")
                                        if p['statut'] == "EN_COURS": st.caption(f"• 🟠 :orange[**En panne** depuis {h_debut}]")
                                    elif est_en_interruption and not a_deja_ouvert:
                                        st.write(f"• 🟣 :violet[**Ouverture retardée**]")
                                        st.caption(f"• 🕒 Stand-by depuis {h_ouverture_theorique.strftime('%H:%M')}")
                                    elif p['statut'] == "EN_COURS":
                                        st.write(f"• 🟠 :orange[**En cours** depuis {h_debut}]")
                                    elif p['statut'] == "TERMINEE":
                                        st.write(f"• 🟢 :green[**Opérationnel** depuis {p['fin'].strftime('%H:%M')}]")
                                        if p['debut'].time() <= h_ouverture_theorique:
                                            st.caption(f"• 🟣 :violet[**Ouverture retardée**] (Prévue à {h_ouverture_theorique.strftime('%H:%M')})")
                                        else:
                                            st.caption(f"• 🔴 :red[**En panne** à {h_debut}] ({p['duree']} min)")
                                else:
                                    if p['statut'] == "TERMINEE":
                                        h_fin = p['fin'].strftime('%H:%M')
                                        if p['debut'].time() <= h_ouverture_theorique:
                                            st.caption(f"• 🟢 :green[**Opérationnel à {h_fin}**] | 🟣 :violet[**Ouverture retardée**]")
                                        else:
                                            st.caption(f"• 🟢 :green[**Opérationnel à {h_fin}**] ({p['duree']} min)")
                                            st.caption(f"• 🔴 :red[**En panne à {h_debut}**]")
                                if idx < len(pannes_triees) - 1: 
                                    st.markdown("<hr style='margin: 5px 0px 5px 0px; opacity: 0.2;'>", unsafe_allow_html=True)
                        else: 
                            if est_definitivement_ferme:
                                st.write(f"• 🔴 :red[**Fermé à {heure_fermeture_constatee}**]")
                            elif est_en_interruption and not a_deja_ouvert:
                                st.write(f"• 🟣 :violet[**Ouverture retardée**]")
                                st.caption(f"• 🕒 Stand-by depuis {h_ouverture_theorique.strftime('%H:%M')}")
                            else:
                                st.write("✅ **Aucun incident signalé**")
            st.divider()

st.subheader("🚨 Dernières interruptions")
if not df_pannes_brutes.empty:
    df_pannes_brutes['start_time_dt'] = pd.to_datetime(df_pannes_brutes['start_time'])
    flux = df_pannes_brutes[df_pannes_brutes['start_time_dt'] >= debut_journee].copy()
    flux['end_time_dt'] = pd.to_datetime(flux['end_time'])
    flux['duree'] = (flux['end_time_dt'] - flux['start_time_dt']).dt.total_seconds() / 60
    flux = flux[(flux['end_time'].isna()) | (flux['duree'] >= 3)]
    flux = flux.sort_values('start_time', ascending=False)
    flux = flux.drop_duplicates(subset=['ride_name']).head(5)
    
    for _, p in flux.iterrows():
        d_p = pd.to_datetime(p['start_time']).astimezone(paris_tz)
        if pd.isna(p['end_time']):
            st.error(f"🔴 {p['ride_name']} >> depuis {d_p.strftime('%H:%M')}")
        else:
            f_p = pd.to_datetime(p['end_time']).astimezone(paris_tz)
            st.success(f"✅ {p['ride_name']} >> fini à {f_p.strftime('%H:%M')}")
else:
    st.warning("📭 Aucune donnée live disponible.")

st.divider()
st.caption("Disney Wait Time Tool | Real-time Dashboard")
