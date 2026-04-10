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
from config import PARK_OPENING, DLP_CLOSING, DAW_CLOSING, EMT_OPENING
from special_hours import ANTICIPATED_CLOSINGS, FANTASYLAND_EARLY_CLOSE, EMT_EARLY_OPEN

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Disney Wait Time", page_icon="🏰", layout="centered")

# --- STYLE CSS GLOBAL & MAGIQUE ---
st.markdown("""
<style>
    /* --- OPTIMISATION DU LAYOUT (ANTI-SAUT) --- */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        padding-left: 2rem;
        padding-right: 2rem;
        max-width: 100% !important; /* Force le Full Width immédiatement */
    }

    /* --- RESPONSIVE : CARTES ET COLONNES --- */
    @media (max-width: 768px) {
        .block-container {
            padding-left: 0.5rem;
            padding-right: 0.5rem;
        }
        .ride-left-card {
            padding: 8px 10px;
            height: 60px; /* Un peu plus compact sur mobile */
        }
        .ride-right-wait {
            min-width: 65px;
            height: 60px;
        }
        .ride-main-name { font-size: 12px; }
        .wait-val { font-size: 18px; }
    }

    /* --- DESIGN DES BADGES ET CARTES --- */
    .ride-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px; width: 100%; gap: 10px; }
    .ride-left-card { border-radius: 16px; padding: 10px 15px; display: flex; align-items: center; justify-content: space-between; flex-grow: 1; height: 68px; }
    .ride-info-meta { display: flex; align-items: center; gap: 12px; }
    .ride-titles { display: flex; flex-direction: column; }
    .ride-main-name { color: white; font-size: 14px; font-weight: 600; margin: 0; line-height: 1.2; }
    .ride-sub-status { color: rgba(255,255,255,0.7); font-size: 11px; margin: 0; }
    .state-pill { background: rgba(0,0,0,0.3); color: white; font-size: 10px; font-weight: 700; padding: 2px 8px; border-radius: 20px; text-transform: uppercase; border: 1px solid rgba(255,255,255,0.1); }
    .ride-right-wait { min-width: 75px; height: 68px; border-radius: 16px; display: flex; flex-direction: column; align-items: center; justify-content: center; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .wait-val { font-size: 20px; font-weight: 800; line-height: 1; }
    .wait-unit { font-size: 10px; font-weight: 400; opacity: 0.8; }

    /* --- COULEURS DES CARTES --- */
    .card-green { background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.3); }
    .card-orange { background: rgba(245, 158, 11, 0.15); border: 1px solid rgba(245, 158, 11, 0.3); }
    .card-blue { background: rgba(59, 130, 246, 0.15); border: 1px solid rgba(59, 130, 246, 0.3); }
    .card-grey { background: rgba(107, 114, 128, 0.15); border: 1px solid rgba(107, 114, 128, 0.3); }
    .card-bordeaux { background: rgba(153, 27, 27, 0.15); border: 1px solid rgba(153, 27, 27, 0.3); }
    .bg-green { background: #10b981; }
    .bg-orange { background: #f59e0b; }
    .bg-blue { background: #3b82f6; }
    .bg-grey { background: #6b7280; }
    .bg-bordeaux { background: #991b1b; }

    /* --- ANIMATIONS ET POPOVER --- */
    @keyframes shine { to { background-position: 200% center; } }
    .magic-title {
        text-align: center;
        background: linear-gradient(120deg, #4facfe 0%, #00f2fe 50%, #4facfe 100%);
        background-size: 200% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800; font-size: 28px; margin-bottom: 25px;
        animation: shine 3s linear infinite;
    }
    .cat-badge-magic {
        padding: 8px 20px; border-radius: 50px; font-size: 14px; font-weight: 700;
        display: block; text-align: center; margin: 20px 0 10px 0; text-transform: uppercase;
    }
    .bg-blue-magic { background: linear-gradient(45deg, #4facfe, #00f2fe); color: white; }
    .bg-green-magic { background: linear-gradient(45deg, #43e97b, #38f9d7); color: white; }
    .bg-orange-magic { background: linear-gradient(45deg, #f9d423, #ff4e50); color: white; }
    .shortcut-card {
        background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px); border-radius: 15px; padding: 12px; margin-bottom: 10px; transition: 0.3s;
    }
    .shortcut-card:hover { transform: translateY(-3px); background: rgba(255, 255, 255, 0.08); }
    
    /* Harmonisation des codes dans le popover */
    code { color: #4facfe !important; background: rgba(79, 172, 254, 0.1) !important; }
</style>
""", unsafe_allow_html=True)

# --- INITIALISATION ---
st.write(" ")
st.title("🏰 Disney Wait Time")
paris_tz = pytz.timezone('Europe/Paris')
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = datetime.now(paris_tz).strftime("%H:%M:%S")

st_autorefresh(interval=60000, key="datarefresh")
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def trigger_github_action():
    REPO, WORKFLOW_ID, TOKEN = "momoF07/disney-tracker", "check.yml", st.secrets["GITHUB_TOKEN"]
    url = f"https://api.github.com/repos/{REPO}/actions/workflows/{WORKFLOW_ID}/dispatches"
    headers = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        res = requests.post(url, headers=headers, json={"ref": "main"})
        return res.status_code
    except: return 500

# --- DATA RECOVERY ---
maintenant = datetime.now(paris_tz)
heure_actuelle = maintenant.time()
heure_reset = maintenant.replace(hour=2, minute=30, second=0, microsecond=0)
debut_journee = heure_reset if maintenant >= heure_reset else heure_reset - timedelta(days=1)

try:
    resp_live = supabase.table("disney_live").select("*").execute()
    df_live = pd.DataFrame(resp_live.data)
    resp_status = supabase.table("daily_status").select("*").execute()
    status_map = {item['ride_name']: item for item in resp_status.data} if resp_status.data else {}
    resp_101 = supabase.table("logs_101").select("*").gte("start_time", debut_journee.isoformat()).execute()
    df_pannes_brutes = pd.DataFrame(resp_101.data)
    derniere_maj = pd.to_datetime(df_live['updated_at']).dt.tz_convert('Europe/Paris').max().strftime("%H:%M:%S") if not df_live.empty else "--:--:--"
except: st.error("Erreur base de données")

all_pannes = []
if not df_live.empty and not df_pannes_brutes.empty:
    for _, row in df_pannes_brutes.iterrows():
        d_p = pd.to_datetime(row['start_time']).astimezone(paris_tz)
        f_p = pd.to_datetime(row['end_time']).astimezone(paris_tz) if pd.notna(row['end_time']) else None
        all_pannes.append({"ride": row['ride_name'], "debut": d_p, "fin": f_p, "statut": "EN_COURS" if f_p is None else "TERMINEE", "duree": int((f_p - d_p).total_seconds() / 60) if f_p else 0})

# --- HEADER INFO ---
header_html = f"""
<div style="background:rgba(255,255,255,0.05); padding:12px; border-radius:15px; border-left:4px solid #4facfe; margin-bottom:15px;">
    <div style="display:flex; justify-content:space-between; width:100%;">
        <div><span style="color:#94a3b8; font-size:12px;">API:</span> <b style="color:white;">{derniere_maj}</b></div>
        <div><span style="color:#94a3b8; font-size:12px;">Refresh:</span> <b style="color:white;">{st.session_state.last_refresh}</b></div>
    </div>
</div>
"""
st.markdown(header_html, unsafe_allow_html=True)

col_btn1, col_btn2 = st.columns(2)
with col_btn1:
    if st.button('✨ Actualiser', use_container_width=True): st.rerun()
with col_btn2:
    if st.button('🚀 Relevé manuel', type="primary", use_container_width=True):
        if trigger_github_action() == 204: st.toast("🚀 Requête envoyée !"); time_sleep.sleep(40); st.rerun()

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Disney Live Board", page_icon="🏰", layout="wide")

# --- FILTRES & INDEX ---
st.write("---")
col_sc, col_help = st.columns([0.88, 0.12])

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
    res = get_rides_by_zone(sc, sorted(df_live['ride_name'].unique()) if not df_live.empty else [], all_pannes)
    if res: 
        current_selection = res
        st.toast(f"🪄 Sortilège **{sc}** activé !", icon="✨")

if not df_live.empty:
    options = sorted(df_live['ride_name'].unique())
    selected_options = st.multiselect("📍 Sélection :", options=options, default=[i for i in current_selection if i in options], format_func=lambda x: f"{get_emoji(x)} {x}")
    st.query_params["fav"] = selected_options

    if selected_options:
        # --- BARRE DE TRI ÉLÉGANTE ---
        st.write("")
        col_sort, col_dir = st.columns([0.82, 0.18])
        
        with col_sort:
            sort_mode = st.segmented_control(
                "Affichage :",
                # Ajout de l'option Réhabilitations
                options=["🔠 Nom", "⏳ Temps d'Attente", "⚠️ Incidents", "🛠️ Réhabilitations"],
                default="🔠 Nom",
                key="sort_selector",
                label_visibility="collapsed"
            )
        
        with col_dir:
            descending = st.toggle("↕️", value=False, help="Inverser l'ordre")
    
        # --- LOGIQUE DE TRI ET FILTRAGE ---
        
        # 1. Filtre Temps d'Attente (Uniquement les ouvertes)
        if sort_mode == "⏳ Temps d'Attente":
            selected_options = [r for r in selected_options if df_live[df_live['ride_name'] == r]['is_open'].iloc[0]]
            selected_options = sorted(selected_options, key=lambda x: df_live[df_live['ride_name'] == x]['wait_time'].iloc[0], reverse=descending)
            if not selected_options: st.info("🕒 Aucune attraction ouverte dans cette sélection.")
        
        # 2. Filtre Incidents (Pannes et retards, hors rehabs et fermetures nuit)
        elif sort_mode == "⚠️ Incidents":
            def is_real_incident(r_n):
                r_d = df_live[df_live['ride_name'] == r_n].iloc[0]
                r_i = status_map.get(r_n, {})
                h_f_c = ANTICIPATED_CLOSINGS.get(r_n) or (DAW_CLOSING if any(a.lower() in r_n.lower() for a in RIDES_DAW) else DLP_CLOSING)
                # Pas ouvert ET pas en rehab ET parc encore ouvert
                est_en_rehab = not r_i.get('opened_yesterday', True) and not r_i.get('has_opened_today', False)
                return not r_d['is_open'] and not est_en_rehab and heure_actuelle < h_f_c
                
            selected_options = [r for r in selected_options if is_real_incident(r)]
            selected_options = sorted(selected_options, reverse=descending)
            if not selected_options: st.success("🌟 Aucun incident à signaler sur cette sélection.")
    
        # 3. NOUVEAU : Filtre Réhabilitations
        elif sort_mode == "🛠️ Réhabilitations":
            def is_in_rehab(r_n):
                r_i = status_map.get(r_n, {})
                r_d = df_live[df_live['ride_name'] == r_n].iloc[0]
                # Logique : Pas ouvert hier ET pas ouvert aujourd'hui ET actuellement fermé
                return not r_i.get('opened_yesterday', True) and not r_i.get('has_opened_today', False) and not r_d['is_open']
                
            selected_options = [r for r in selected_options if is_in_rehab(r)]
            selected_options = sorted(selected_options, reverse=descending)
            if not selected_options: st.info("✅ Aucune réhabilitation en cours sur cette sélection.")
        
        # 4. Tri par Nom (Par défaut)
        else:
            selected_options = sorted(selected_options, reverse=descending)
    
        st.write("") # Espace final avant les cartes

        for ride in selected_options:
            data = df_live[df_live['ride_name'] == ride].iloc[0]
            info = status_map.get(ride, {})
            panne_act = next((p for p in all_pannes if p['ride'] == ride and p['statut'] == "EN_COURS"), None)
            
            is_daw = any(a.lower() in ride.lower() for a in RIDES_DAW)
            h_o, h_f = (EMT_OPENING if ride in EMT_EARLY_OPEN else PARK_OPENING), (DAW_CLOSING if is_daw else DLP_CLOSING)
            if ride in ANTICIPATED_CLOSINGS: h_f = ANTICIPATED_CLOSINGS[ride]
            elif ride in FANTASYLAND_EARLY_CLOSE: h_f = (datetime.combine(datetime.today(), DLP_CLOSING) - timedelta(minutes=65)).time()

            rehab = not info.get('opened_yesterday', True) and not info.get('has_opened_today', False) and not data['is_open']
            if data['is_open'] and data['wait_time'] > 0: rehab = False

            if rehab: sub, wait, bg, card_style, pill = "🛠️ Travaux détectés", "REHAB", "bg-grey", "card-grey", "TRAVAUX"
            elif heure_actuelle >= h_f and not data['is_open']: sub, wait, bg, card_style, pill = f"🏁 Fermé à {h_f.strftime('%H:%M')}", "- - -", "bg-bordeaux", "card-bordeaux", "FERMÉ"
            elif heure_actuelle < h_o and not data['is_open']: sub, wait, bg, card_style, pill = "🕒 En attente", "- - -", "bg-blue", "card-blue", "ATTENTE"
            elif not data['is_open']: sub, wait, bg, card_style, pill = f"⚠️ Panne depuis {panne_act['debut'].strftime('%H:%M')}" if panne_act else "⚠️ Interruption", "- - -", "bg-orange", "card-orange", "INCIDENT"
            else: sub, wait, bg, card_style, pill = "✅ Opérationnel", f"{int(data['wait_time'])}", "bg-green", "card-green", "OUVERT"

            wait_html = f'<span class="wait-val">{wait}</span>' if wait in ["- - -", "REHAB"] else f'<span class="wait-val">{wait}</span><span class="wait-unit">min</span>'
            st.markdown(f"""<div class="ride-row"><div class="ride-left-card {card_style}"><div class="ride-info-meta"><span style="font-size:24px;">{get_emoji(ride)}</span><div class="ride-titles"><p class="ride-main-name">{ride}</p><p class="ride-sub-status">{sub}</p></div></div><div class="state-pill">{pill}</div></div><div class="ride-right-wait {bg}"><span style="font-size:10px; opacity:0.7;">ATTENTE</span>{wait_html}</div></div>""", unsafe_allow_html=True)

            with st.expander("📜 Historique"):
                if rehab: 
                    st.write("• 🛠️ :grey[**Maintenance en cours**]")
                else:
                    # 1. On récupère les pannes (sécurité 2min)
                    h_p_clean = [p for p in all_pannes if p['ride'] == ride and (p['statut'] == "EN_COURS" or p['duree'] >= 2)]
                    pannes_triees = sorted(h_p_clean, key=lambda x: x['debut'], reverse=True)
                    
                    # 2. Analyse pour le Delayed Opening (DO)
                    a_ouvert_aujourdhui = info.get('has_opened_today', False)
                    # On cherche la toute première panne de la journée
                    premiere_panne = sorted(h_p_clean, key=lambda x: x['debut'])[0] if h_p_clean else None
                    
                    # Un DO historique est détecté si la première panne a commencé à l'heure d'ouverture (ou avant)
                    est_un_do_historique = premiere_panne and premiere_panne['debut'].time() <= h_o
                    
                    # Un DO "en cours" (pour l'affichage live)
                    est_en_retard_live = (heure_actuelle > h_o) and (heure_actuelle < h_f) and not a_ouvert_aujourdhui and not data['is_open']

                    if h_p_clean or est_en_retard_live:
                        # --- 1. AFFICHAGE ÉTAT ACTUEL ---
                        if est_en_retard_live:
                            st.write(f"• 🟣 :violet[**Ouverture retardée**] (Prévue à {h_o.strftime('%H:%M')})")
                            st.caption(f"&nbsp;&nbsp;&nbsp;&nbsp;└ 🕒 En attente de mise en service")
                        
                        elif pannes_triees:
                            p_actuelle = pannes_triees[0]
                            h_d_act = p_actuelle['debut'].strftime('%H:%M')
                            
                            if heure_actuelle >= h_f and not data['is_open']: 
                                st.write("• 🔴 :red[**Fermé pour la nuit**]")
                            elif p_actuelle['statut'] == "EN_COURS": 
                                st.write(f"• 🟠 :orange[**En cours** depuis {h_d_act}]")
                            else: 
                                # Si l'attraction est ouverte, on affiche le dernier événement (qui peut être la fin d'un DO)
                                st.write(f"• 🟢 :green[**Opérationnel** à {p_actuelle['fin'].strftime('%H:%M')}]")
                                if p_actuelle['debut'].time() <= h_o:
                                    st.caption(f"&nbsp;&nbsp;&nbsp;&nbsp;└ 🟣 :violet[**Ouverture retardée**] (Prévue à {h_o.strftime('%H:%M')})")
                                else:
                                    st.caption(f"&nbsp;&nbsp;&nbsp;&nbsp;└ 🔴 :red[**Panne** à {h_d_act}] ({p_actuelle['duree']} min)")

                        # --- 2. AFFICHAGE DU RESTE DE L'HISTORIQUE ---
                        if len(pannes_triees) > 1:
                            for p in pannes_triees[1:]:
                                h_d = p['debut'].strftime('%H:%M')
                                if p['statut'] == "TERMINEE":
                                    # Si cette panne passée était le DO du matin
                                    if p['debut'].time() <= h_o:
                                        st.caption(f"• 🟢 :green[**Ope à {p['fin'].strftime('%H:%M')}**] | 🟣 :violet[**Retard d'ouverture**]")
                                    else:
                                        st.caption(f"• 🟢 :green[**Ope à {p['fin'].strftime('%H:%M')}**] | 🔴 :red[**Panne à {h_d}**] ({p['duree']} min)")
                    else: 
                        st.write("✅ Aucun incident aujourd'hui.")
st.subheader("🚨 Dernières interruptions")
if not df_pannes_brutes.empty:
    flux = df_pannes_brutes[pd.to_datetime(df_pannes_brutes['start_time']).dt.tz_convert('Europe/Paris') >= debut_journee].copy()
    flux = flux.sort_values('start_time', ascending=False).drop_duplicates(subset=['ride_name']).head(5)
    for _, p in flux.iterrows():
        r_n, d_p = p['ride_name'], pd.to_datetime(p['start_time']).astimezone(paris_tz)
        h_f_p = pd.to_datetime(p['end_time']).astimezone(paris_tz).strftime("%H:%M") if pd.notna(p['end_time']) else None
        h_f_c = ANTICIPATED_CLOSINGS.get(r_n) or (DAW_CLOSING if any(a.lower() in r_n.lower() for a in RIDES_DAW) else DLP_CLOSING)
        if not h_f_p:
            if heure_actuelle >= h_f_c: st.markdown(f'<div class="ride-left-card card-bordeaux" style="width:100%; margin-bottom:10px;"><div class="ride-info-meta"><span>{get_emoji(r_n)}</span><div class="ride-titles"><p class="ride-main-name">{r_n}</p><p class="ride-sub-status">Fermeture nocturne</p></div></div><div class="state-pill">FERMETURE</div></div>', unsafe_allow_html=True)
            else: st.markdown(f'<div class="ride-left-card card-orange" style="width:100%; margin-bottom:10px;"><div class="ride-info-meta"><span>{get_emoji(r_n)}</span><div class="ride-titles"><p class="ride-main-name">{r_n}</p><p class="ride-sub-status">En panne à {d_p.strftime("%H:%M")}</p></div></div><div class="state-pill">INTERRUPTION</div></div>', unsafe_allow_html=True)
        else: st.markdown(f'<div class="ride-left-card card-green" style="width:100%; margin-bottom:10px;"><div class="ride-info-meta"><span>{get_emoji(r_n)}</span><div class="ride-titles"><p class="ride-main-name">{r_n}</p><p class="ride-sub-status">Réouvert à {h_f_p}</p></div></div><div class="state-pill">REOUVERTURE</div></div>', unsafe_allow_html=True)

st.caption("Disney Wait Time Tool | Dashboard v3.1")
