# --- IMPORTS ---
import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime, timedelta, time
import pytz
import requests
import time as time_sleep
from streamlit_autorefresh import st_autorefresh 

# --- IMPORTS DES MODULES ---
from ui.styles import apply_custom_style
from ui.comp import render_weather_card, render_ride_card, render_api_info
from ui.popup import render_shortcuts_popover, render_history_expander
from modules.weather import get_disney_weather
from modules.emojis import get_emoji, get_rides_by_zone, RIDES_DLP, RIDES_DAW
from modules.special_hours import ANTICIPATED_CLOSINGS, FANTASYLAND_EARLY_CLOSE, EMT_EARLY_OPEN
from config import PARK_OPENING, DLP_CLOSING, DAW_CLOSING, EMT_OPENING
from ui.filters import render_quick_filters

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Disney Live Board", 
    page_icon="🏰", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Application du CSS personnalisé
apply_custom_style()

# --- GESTION DU TEMPS & REFRESH ---
paris_tz = pytz.timezone('Europe/Paris')
maintenant = datetime.now(paris_tz)
heure_refresh = maintenant.strftime("%H:%M:%S") 

st.session_state.last_refresh = heure_refresh
st_autorefresh(interval=60000, key="datarefresh")

# --- CONNEXION SUPABASE ---
@st.cache_resource
def init_connection():
    """Initialise et met en cache la connexion Supabase"""
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_connection()

# --- FONCTION GITHUB ACTION ---
def trigger_github_action():
    """Déclenche le workflow de scraping sur GitHub Actions"""
    REPO = "momoF07/disney-tracker"
    WORKFLOW_ID = "check.yml"
    TOKEN = st.secrets["GITHUB_TOKEN"]
    url = f"https://api.github.com/repos/{REPO}/actions/workflows/{WORKFLOW_ID}/dispatches"
    headers = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        res = requests.post(url, headers=headers, json={"ref": "main"})
        return res.status_code
    except Exception as e:
        st.error(f"Erreur GitHub Action: {e}")
        return 500

# --- DÉBUT DE L'INTERFACE ---
st.write("") 
st.title("🏰 Disney Wait Time")

# --- DATA RECOVERY ---
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
except Exception as e:
    st.error(f"❌ Erreur base de données : {e}")
    df_live, df_pannes_brutes = pd.DataFrame(), pd.DataFrame()

all_pannes = []
if not df_live.empty and not df_pannes_brutes.empty:
    for _, row in df_pannes_brutes.iterrows():
        d_p = pd.to_datetime(row['start_time']).astimezone(paris_tz)
        f_p = pd.to_datetime(row['end_time']).astimezone(paris_tz) if pd.notna(row['end_time']) else None
        all_pannes.append({
            "ride": row['ride_name'], "debut": d_p, "fin": f_p, 
            "statut": "EN_COURS" if f_p is None else "TERMINEE", 
            "duree": int((f_p - d_p).total_seconds() / 60) if f_p else 0
        })

# --- BLOC METEO ---
render_weather_card(get_disney_weather())

# --- HEADER INFO ---
render_api_info(derniere_maj, st.session_state.last_refresh)

st.markdown('<div class="action-buttons-container">', unsafe_allow_html=True)
col_btn1, col_btn2 = st.columns(2)
with col_btn1:
    if st.button('✨ Actualiser', use_container_width=True): 
        st.rerun()
with col_btn2:
    if st.button('🚀 Relevé manuel', type="primary", use_container_width=True):
        if trigger_github_action() == 204: 
            st.toast("🚀 Requête envoyée !")
            time_sleep.sleep(40)
            st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

# --- 1. DÉFINITION DES VARIABLES DE BASE ---
current_selection = st.query_params.get_all("fav")

options = sorted(df_live['ride_name'].unique()) if not df_live.empty else []

render_quick_filters(options, all_pannes, heure_actuelle)

# --- 3. SÉLECTION MULTIPLE ---
if not df_live.empty:
    st.markdown('<div class="selection-container">', unsafe_allow_html=True)
    
    with st.container():
        # Utilise 'options' défini en haut
        selected_options = st.multiselect(
            "📍 VOTRE SÉLECTION", 
            options=options, 
            default=[i for i in current_selection if i in options], 
            format_func=lambda x: f"{get_emoji(x)} {x}",
            placeholder="Ajouter une attraction..."
        )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Mise à jour de l'URL pour garder les favoris au prochain refresh
    st.query_params["fav"] = selected_options

    if selected_options:
        st.markdown('<div class="sort-container">', unsafe_allow_html=True)
        
        # --- LIGNE 1 : CRITÈRE DE TRI ---
        st.markdown('<p class="sort-label">Filtrer par</p>', unsafe_allow_html=True)
        sort_mode = st.segmented_control(
            "Critère",
            options=["🔠 Nom", "⏳ Attente", "⚠️ Incidents", "🛠️ Rehab"],
            default="🔠 Nom",
            key="sort_selector",
            label_visibility="collapsed"
        )

        # --- LIGNE 2 : ORDRE DE TRI (CONDITIONNEL) ---
        # On ne l'affiche que si on est en mode Nom ou Attente
        if sort_mode in ["🔠 Nom", "⏳ Attente"]:
            if sort_mode == "⏳ Attente":
                order_options = ["- Attente", "+ Attente"]
            else:
                order_options = ["A → Z", "Z → A"]

            st.markdown('<p class="order-label">Ordre d\'affichage</p>', unsafe_allow_html=True)
            order_selection = st.segmented_control(
                "Ordre",
                options=order_options,
                default=order_options[0],
                key="order_selector_dynamic",
                label_visibility="collapsed"
            )
            # Définition de is_desc basée sur le widget
            is_desc = order_selection in ["+ Attente", "Z → A"]
        else:
            # Valeur par défaut pour Incidents et Rehab (toujours True pour mettre en haut)
            is_desc = True 
            # On définit order_selection à None pour éviter les erreurs de variable inexistante
            order_selection = None

        st.markdown('</div>', unsafe_allow_html=True)

        # --- LOGIQUE DE TRI ---
        st.session_state.desc_order = is_desc

        if sort_mode == "⏳ Attente":
            opened = [r for r in selected_options if df_live[df_live['ride_name'] == r]['is_open'].iloc[0]]
            closed = [r for r in selected_options if not df_live[df_live['ride_name'] == r]['is_open'].iloc[0]]
            selected_options = sorted(opened, key=lambda x: df_live[df_live['ride_name'] == x]['wait_time'].iloc[0], reverse=is_desc) + closed

        elif sort_mode == "⚠️ Incidents":
            # Tri : Incidents en haut, puis alphabétique pour le reste
            selected_options = sorted(
                selected_options, 
                key=lambda r: (any(p['ride'] == r and p['statut'] == "EN_COURS" for p in all_pannes), r), 
                reverse=is_desc # True (en panne) sera en haut
            )

        elif sort_mode == "🛠️ Rehab":
            # Tri : Rehab en haut, puis alphabétique
            selected_options = sorted(
                selected_options, 
                key=lambda r: (not status_map.get(r, {}).get('opened_yesterday', True), r), 
                reverse=is_desc
            )

        else: # Mode Nom
            selected_options = sorted(selected_options, reverse=is_desc)

    # --- BOUCLE D'AFFICHAGE ---
    for ride in selected_options:
        ride_data = df_live[df_live['ride_name'] == ride]
        if ride_data.empty: continue
        
        data = ride_data.iloc[0]
        info = status_map.get(ride, {})
        panne_act = next((p for p in all_pannes if p['ride'] == ride and p['statut'] == "EN_COURS"), None)
        
        # --- 1. CALCUL DE L'HEURE DE FERMETURE (h_f) ---
        is_daw = any(a.lower() in ride.lower() for a in RIDES_DAW)
        
        if ride in ANTICIPATED_CLOSINGS:
            h_f = ANTICIPATED_CLOSINGS[ride]
        elif ride in FANTASYLAND_EARLY_CLOSE:
            # Calcul : DLP_CLOSING - 1 heure
            base_h = DLP_CLOSING.hour
            base_m = DLP_CLOSING.minute
            # On recrée l'heure avec une heure en moins
            h_f = time(base_h - 1, base_m)
        else:
            h_f = DAW_CLOSING if is_daw else DLP_CLOSING
        
        h_o = EMT_OPENING if ride in EMT_EARLY_OPEN else PARK_OPENING
        
        # --- 2. DÉTERMINATION DU STATUT (LOGIQUE PRIORISÉE) ---
        rehab_flag = not info.get('opened_yesterday', True) and not info.get('has_opened_today', False) and not data['is_open']
        
        # PRIORITÉ 1 : Travaux
        if rehab_flag: 
            sub, wait, bg, style, pill = "🛠️ Travaux détectés", "REHAB", "bg-grey", "card-grey", "TRAVAUX"
        
        # PRIORITÉ 2 : Fermeture (On retire le "and not data['is_open']" pour plus de fiabilité)
        # Si l'heure actuelle dépasse h_f, c'est FERMÉ (même si l'API n'est pas encore à jour)
        elif heure_actuelle >= h_f: 
            sub, wait, bg, style, pill = f"🏁 Fermé à {h_f.strftime('%H:%M')}", "- - -", "bg-bordeaux", "card-bordeaux", "FERMÉ"
        
        # PRIORITÉ 3 : Avant l'ouverture
        elif heure_actuelle < h_o and not data['is_open']: 
            sub, wait, bg, style, pill = "🕒 En attente", "- - -", "bg-blue", "card-blue", "ATTENTE"
        
        # PRIORITÉ 4 : Incident (Seulement si on est dans les horaires d'ouverture)
        elif not data['is_open']: 
            sub, wait, bg, style, pill = f"⚠️ Panne depuis {panne_act['debut'].strftime('%H:%M')}" if panne_act else "⚠️ Interruption", "- - -", "bg-orange", "card-orange", "INCIDENT"
        
        # PAR DÉFAUT : Ouvert
        else: 
            sub, wait, bg, style, pill = "✅ Opérationnel", int(data['wait_time']), "bg-green", "card-green", "OUVERT"

        # --- 3. AFFICHAGE ---
        render_ride_card(ride, sub, wait, bg, style, pill)
        
        with st.expander("📜 Historique"):
            h_p_clean = [p for p in all_pannes if p['ride'] == ride and (p['statut'] == "EN_COURS" or p['duree'] >= 2)]
            p_triees = sorted(h_p_clean, key=lambda x: x['debut'], reverse=True)
            do_live = (heure_actuelle > h_o) and (heure_actuelle < h_f) and not info.get('has_opened_today', False) and not data['is_open']
            render_history_expander(ride, rehab_flag, h_p_clean, p_triees, do_live, h_o, h_f, data['is_open'])

# --- DERNIÈRES INTERRUPTIONS & ACTUALITÉS ---
st.write("---")
st.subheader("🚨 Flux des activités")

if not df_pannes_brutes.empty:
    flux = df_pannes_brutes.copy()
    flux['dt'] = pd.to_datetime(flux['start_time'])
    flux = flux[flux['dt'].dt.tz_convert('Europe/Paris') >= debut_journee]
    flux = flux.sort_values('dt', ascending=False).drop_duplicates(subset=['ride_name']).head(5)
    
    for _, p in flux.iterrows():
        r_n = p['ride_name']
        d_p = pd.to_datetime(p['start_time']).astimezone(paris_tz)
        h_f_p = pd.to_datetime(p['end_time']).astimezone(paris_tz).strftime("%H:%M") if pd.notna(p['end_time']) else None
        
        # --- CALCUL DE L'HEURE DE FERMETURE (pour filtrage actu) ---
        is_daw_p = any(a.lower() in r_n.lower() for a in RIDES_DAW)
        if r_n in ANTICIPATED_CLOSINGS: h_f_limit = ANTICIPATED_CLOSINGS[r_n]
        elif r_n in FANTASYLAND_EARLY_CLOSE: h_f_limit = time(DLP_CLOSING.hour - 1, DLP_CLOSING.minute)
        else: h_f_limit = DAW_CLOSING if is_daw_p else DLP_CLOSING

        # 1. CAS FERMETURE DÉFINITIVE (Si l'heure actuelle a dépassé l'heure de fermeture)
        if heure_actuelle >= h_f_limit:
            render_ride_card(
                ride=r_n, 
                sub=f"Fermeture journalière à {h_f_limit.strftime('%H:%M')}", 
                wait="FIN", 
                bg="bg-bordeaux", 
                card_style="card-bordeaux", 
                pill="FERMETURE", 
                show_wait=False
            )

        # 2. CAS PANNE EN COURS
        elif not h_f_p:
            render_ride_card(
                ride=r_n, 
                sub=f"En panne à {d_p.strftime('%H:%M')}", 
                wait="101", 
                bg="bg-orange", 
                card_style="card-orange", 
                pill="INTERRUPTION", 
                show_wait=False
            )

        # 3. CAS RÉOUVERTURE
        else:
            render_ride_card(
                ride=r_n, 
                sub=f"Réouvert à {h_f_p}", 
                wait="OK", 
                bg="bg-green", 
                card_style="card-green", 
                pill="REOUVERTURE", 
                show_wait=False
            )
st.caption(f"Disney Wait Time Tool | v4.0 | Refresh: {st.session_state.last_refresh}")