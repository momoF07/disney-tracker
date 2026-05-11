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
from ui.comp import render_weather_card, render_ride_card, render_api_info, render_park_hours, render_upcoming_shows
from ui.popup import render_shortcuts_popover, render_history_expander
from modules.rehabilitations import REHAB_LIST
from modules.weather import get_disney_weather, get_maintenance_weather
from modules.emojis import get_emoji, get_rides_by_zone, RIDES_DLP, RIDES_DAW, PARKS_DATA
from modules.special_hours import ANTICIPATED_CLOSINGS, FANTASYLAND_EARLY_CLOSE, EMT_EARLY_OPEN, SPECIAL_OPENING_HOURS
from config import PARK_OPENING, DLP_CLOSING, DAW_CLOSING, EMT_OPENING
from ui.filters import render_quick_filters
from maintenance import show_maintenance

# --- VERSION ---
webversion = "v5.3"

# --- RÉFÉRENTIEL DES ATTRACTIONS ---
ALL_RIDES_LIST = sorted(list(set(RIDES_DLP + RIDES_DAW)))
STATS_EXCLUDED = {
    "Main Street Vehicles",
    "Disneyland Railroad Main Street Station",
    "Disneyland Railroad Frontierland Depot",
}


# 1. Initialisation de la variable de session
if "bypass_maintenance" not in st.session_state:
    st.session_state.bypass_maintenance = False

# 2. Variable de contrôle globale
MAINTENANCE_MODE = False

# 3. Logique de filtrage
if MAINTENANCE_MODE and not st.session_state.bypass_maintenance:
    show_maintenance()

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Disney Live Board",
    page_icon="🏰",
    layout="wide",
    initial_sidebar_state="collapsed"
)

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
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_connection()

# --- FONCTION GITHUB ACTION ---
def trigger_github_action():
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

# --- HELPERS REHAB ---
today = maintenant.date()

def is_in_rehab(ride):
    r = REHAB_LIST.get(ride)
    if not r:
        return False
    debut = r.get('debut')
    fin   = r.get('fin')
    if not debut or not fin:
        return True
    return debut <= today <= fin

def is_during_rehab(row):
    rehab = REHAB_LIST.get(row['ride_name'])
    if not rehab:
        return False
    debut = rehab.get('debut')
    fin   = rehab.get('fin')
    if not debut or not fin:
        return True
    start_date = row['start_dt'].date()
    return debut <= start_date <= fin

# --- DÉBUT DE L'INTERFACE ---
st.write("")
st.title("🏰 Disney Ultime Dashboard")

# --- CONFIGURATION DU FILTRAGE ---
heure_actuelle = maintenant.time()
heure_reset    = maintenant.replace(hour=2, minute=30, second=0, microsecond=0)
debut_journee  = heure_reset if maintenant >= heure_reset else heure_reset - timedelta(days=1)
date_30j       = (maintenant - timedelta(days=30)).isoformat()

# --- VALEURS PAR DÉFAUT ---
derniere_maj    = "--:--:--"
df_live         = pd.DataFrame()
df_pannes_brutes = pd.DataFrame()
status_map      = {}

try:
    resp_live = supabase.table("disney_live").select("*").execute()
    df_live = pd.DataFrame(resp_live.data)

    resp_status = supabase.table("daily_status").select("*").execute()
    status_map = {item['ride_name']: item for item in resp_status.data} if resp_status.data else {}

    resp_101 = supabase.table("logs_101").select("*").gte("start_time", debut_journee.isoformat()).execute()
    df_pannes_brutes = pd.DataFrame(resp_101.data)

    derniere_maj = pd.to_datetime(df_live['updated_at']).dt.tz_convert('Europe/Paris').max().strftime("%H:%M:%S") if not df_live.empty else "--:--:--"

except Exception as e:
    st.error(f"❌ Erreur critique base de données : {e}")

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

# --- BLOC HORAIRES ---
try:
    res = supabase.table("ride_schedules").select("*").execute()
    schedules_data = res.data if res.data else []
except Exception as e:
    st.error(f"Erreur de connexion aux horaires : {e}")
    schedules_data = []

col_h1, col_h2 = st.columns(2)
with col_h1:
    render_park_hours(schedules_data)
with col_h2:
    render_upcoming_shows(schedules_data)

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

# --- SÉLECTION ---
current_selection = st.query_params.get_all("fav")
options = sorted(df_live['ride_name'].unique()) if not df_live.empty else []
render_quick_filters(options, all_pannes, heure_actuelle)

if not df_live.empty:
    st.markdown('<div class="selection-container">', unsafe_allow_html=True)
    with st.container():
        selected_options = st.multiselect(
            "📍 VOTRE SÉLECTION",
            options=options,
            default=[i for i in current_selection if i in options],
            format_func=lambda x: f"{get_emoji(x)} {x}",
            placeholder="Ajouter une attraction..."
        )
    st.markdown('</div>', unsafe_allow_html=True)

    st.query_params["fav"] = selected_options

    if selected_options:
        st.markdown('<div class="sort-container">', unsafe_allow_html=True)

        st.markdown('<p class="sort-label">Filtrer par</p>', unsafe_allow_html=True)
        sort_mode = st.segmented_control(
            "Critère",
            options=["🔠 Nom", "⏳ Attente", "⚠️ Incidents", "🛠️ Rehab"],
            default="🔠 Nom",
            key="sort_selector",
            label_visibility="collapsed"
        )

        if sort_mode in ["🔠 Nom", "⏳ Attente"]:
            order_options = ["- Attente", "+ Attente"] if sort_mode == "⏳ Attente" else ["A → Z", "Z → A"]
            st.markdown('<p class="order-label">Ordre d\'affichage</p>', unsafe_allow_html=True)
            order_selection = st.segmented_control(
                "Ordre",
                options=order_options,
                default=order_options[0],
                key="order_selector_dynamic",
                label_visibility="collapsed"
            )
            is_desc = order_selection in ["+ Attente", "Z → A"]
        else:
            is_desc = True
            order_selection = None

        st.markdown('</div>', unsafe_allow_html=True)
        st.session_state.desc_order = is_desc

        # --- LOGIQUE DE TRI ---
        if sort_mode == "⏳ Attente":
            opened = [r for r in selected_options if df_live[df_live['ride_name'] == r]['is_open'].iloc[0]]
            closed = [r for r in selected_options if not df_live[df_live['ride_name'] == r]['is_open'].iloc[0]]
            selected_options = sorted(opened, key=lambda x: df_live[df_live['ride_name'] == x]['wait_time'].iloc[0], reverse=is_desc) + closed

        elif sort_mode == "⚠️ Incidents":
            has_incidents = any(
                any(p['ride'] == r and p['statut'] == "EN_COURS" for p in all_pannes)
                or any(p['ride'] == r for p in all_pannes)
                for r in selected_options
            )
            if not has_incidents:
                st.markdown(
                    '<div style="display:flex; align-items:center; gap:14px; padding:16px 20px;'
                    'background:rgba(52,211,153,0.06); border:1px solid rgba(52,211,153,0.2);'
                    'border-left:3px solid #34d399; border-radius:16px; margin:8px 0;">'
                    '<span style="font-size:28px; line-height:1;">✅</span>'
                    '<div>'
                    '<div style="font-family:Outfit,sans-serif; font-size:13px; font-weight:700;'
                    'color:#34d399; margin-bottom:2px;">Rien à signaler</div>'
                    '<div style="font-size:11px; color:rgba(255,255,255,0.35); font-weight:400;">'
                    'Aucun incident en cours ou passé sur votre sélection.</div>'
                    '</div></div>',
                    unsafe_allow_html=True
                )
                selected_options = []
            else:
                selected_options = sorted(
                    selected_options,
                    key=lambda r: (any(p['ride'] == r and p['statut'] == "EN_COURS" for p in all_pannes), r),
                    reverse=True
                )

        elif sort_mode == "🛠️ Rehab":
            rides_en_rehab = [r for r in selected_options if is_in_rehab(r)]
            if not rides_en_rehab:
                st.markdown(
                    '<div style="display:flex; align-items:center; gap:14px; padding:16px 20px;'
                    'background:rgba(100,116,139,0.06); border:1px solid rgba(100,116,139,0.2);'
                    'border-left:3px solid #64748b; border-radius:16px; margin:8px 0;">'
                    '<span style="font-size:28px; line-height:1;">🛠️</span>'
                    '<div>'
                    '<div style="font-family:Outfit,sans-serif; font-size:13px; font-weight:700;'
                    'color:#94a3b8; margin-bottom:2px;">Aucune réhabilitation</div>'
                    '<div style="font-size:11px; color:rgba(255,255,255,0.35); font-weight:400;">'
                    'Pas de travaux en cours sur votre sélection.</div>'
                    '</div></div>',
                    unsafe_allow_html=True
                )
                selected_options = []
            else:
                selected_options = sorted(
                    rides_en_rehab,
                    key=lambda r: REHAB_LIST[r].get('debut') or today
                )

        else:
            selected_options = sorted(selected_options, reverse=is_desc)

        # --- BOUCLE D'AFFICHAGE ---
        for ride in selected_options:
            ride_data = df_live[df_live['ride_name'] == ride]
            if ride_data.empty:
                continue

            data      = ride_data.iloc[0]
            info      = status_map.get(ride, {})
            panne_act = next((p for p in all_pannes if p['ride'] == ride and p['statut'] == "EN_COURS"), None)

            # --- HEURE DE FERMETURE ---
            is_daw = any(a.lower() in ride.lower() for a in RIDES_DAW)
            if ride in ANTICIPATED_CLOSINGS:
                h_f = ANTICIPATED_CLOSINGS[ride]
            elif ride in FANTASYLAND_EARLY_CLOSE:
                h_f = time(DLP_CLOSING.hour - 1, DLP_CLOSING.minute)
            else:
                h_f = DAW_CLOSING if is_daw else DLP_CLOSING

            # --- HEURE D'OUVERTURE ---
            h_o = EMT_OPENING if ride in EMT_EARLY_OPEN else PARK_OPENING
            if ride in SPECIAL_OPENING_HOURS:
                h_o = SPECIAL_OPENING_HOURS[ride]

            # --- STATUT ---
            rehab_info = REHAB_LIST.get(ride)
            in_rehab   = is_in_rehab(ride)
            rehab_flag = in_rehab or (
                not info.get('opened_yesterday', True)
                and not info.get('has_opened_today', False)
                and not data['is_open']
            )

            if rehab_flag:
                sub, wait, bg, style, pill = "🛠️ Travaux détectés", "REHAB", "bg-grey", "card-grey", "TRAVAUX"
            elif heure_actuelle >= h_f:
                sub, wait, bg, style, pill = f"🏁 Fermé à {h_f.strftime('%H:%M')}", "F I N", "bg-bordeaux", "card-bordeaux", "FERMÉ"
            elif heure_actuelle < h_o and not data['is_open']:
                sub, wait, bg, style, pill = "🕒 En attente", "- - -", "bg-blue", "card-blue", "ATTENTE"
            elif not data['is_open'] and not info.get('has_opened_today', False):
                sub, wait, bg, style, pill = "⏳ Ouverture retardée", "- - -", "bg-purple", "card-purple", "RETARDÉ"
            elif not data['is_open']:
                sub, wait, bg, style, pill = f"⚠️ Panne depuis {panne_act['debut'].strftime('%H:%M')}" if panne_act else "⚠️ Interruption", "- - -", "bg-orange", "card-orange", "INCIDENT"
            else:
                sub, wait, bg, style, pill = "✅ Opérationnel", int(data['wait_time']), "bg-green", "card-green", "OUVERT"

            # --- FILTRE MODE INCIDENTS : uniquement les pannes en cours ---
            if sort_mode == "⚠️ Incidents":
                if pill not in ("INCIDENT", "RETARDÉ"):
                    continue

            render_ride_card(ride, sub, wait, bg, style, pill)

            if rehab_flag and rehab_info:
                debut     = rehab_info.get('debut')
                debut_str = debut.strftime('🛠️ En réhabilitation depuis le %d/%m —') if debut else ""
                st.caption(f"{debut_str} {rehab_info['msg']}")

            # --- HISTORIQUE : masqué si en réhab ---
            if not rehab_flag:
                with st.expander("📜 Historique"):
                    h_p_clean = [p for p in all_pannes if p['ride'] == ride and (p['statut'] == "EN_COURS" or p['duree'] >= 5)]
                    p_triees  = sorted(h_p_clean, key=lambda x: x['debut'], reverse=True)
                    do_live   = (heure_actuelle > h_o) and (heure_actuelle < h_f) and not info.get('has_opened_today', False) and not data['is_open']
                    render_history_expander(ride, rehab_flag, h_p_clean, p_triees, do_live, h_o, h_f, data['is_open'])

# --- SECTION FLUX & STATISTIQUES ---
st.write("---")
col_flux, col_stats = st.columns([1.2, 1.2], gap="large")

with col_flux:
    st.subheader("🚨 Flux du jour")

    if not df_pannes_brutes.empty:
        flux = df_pannes_brutes.copy()
        flux['dt'] = pd.to_datetime(flux['start_time'])
        flux = flux.sort_values('dt', ascending=False).head(90)

        with st.container(height=425):
            for _, p in flux.iterrows():
                r_n   = p['ride_name']
                d_p   = pd.to_datetime(p['start_time']).astimezone(paris_tz)
                h_f_p = pd.to_datetime(p['end_time']).astimezone(paris_tz).strftime("%H:%M") if pd.notna(p['end_time']) else None

                is_daw_p = any(a.lower() in r_n.lower() for a in RIDES_DAW)
                if r_n in ANTICIPATED_CLOSINGS:
                    h_f_limit = ANTICIPATED_CLOSINGS[r_n]
                elif r_n in FANTASYLAND_EARLY_CLOSE:
                    h_f_limit = time(DLP_CLOSING.hour - 1, DLP_CLOSING.minute)
                else:
                    h_f_limit = DAW_CLOSING if is_daw_p else DLP_CLOSING

                if heure_actuelle >= h_f_limit:
                    render_ride_card(r_n, f"Fermeture à {h_f_limit.strftime('%H:%M')}", "FIN", "bg-bordeaux", "card-bordeaux", "FERMETURE", False)
                elif not h_f_p:
                    render_ride_card(r_n, f"En panne à {d_p.strftime('%H:%M')}", "101", "bg-orange", "card-orange", "INTERRUPTION", False)
                else:
                    render_ride_card(r_n, f"Réouvert à {h_f_p}", "OK", "bg-green", "card-green", "REOUVERTURE", False)
    else:
        st.caption("Aucune activité majeure aujourd'hui.")

with col_stats:
    now_paris     = maintenant
    debut_mois    = now_paris.replace(day=1, hour=2, minute=30, second=0, microsecond=0)
    debut_mois_pr = (debut_mois - pd.DateOffset(months=1)).to_pydatetime()
    fin_mois_pr   = debut_mois
    
    MOIS_FR = {
        1: "Janvier", 2: "Février", 3: "Mars", 4: "Avril",
        5: "Mai", 6: "Juin", 7: "Juillet", 8: "Août",
        9: "Septembre", 10: "Octobre", 11: "Novembre", 12: "Décembre"
    }
    mois_label    = f"{MOIS_FR[now_paris.month]} {now_paris.year}"
    mois_pr_label = f"{MOIS_FR[debut_mois_pr.month]} {debut_mois_pr.year}"

    st.subheader(f"📊 Stats — {mois_label}")

    LAND_COLORS = {
        "MAINSTREET":      "#f59e0b",
        "FRONTIERLAND":    "#ef6c00",
        "ADVENTURELAND":   "#16a34a",
        "FANTASYLAND":     "#9333ea",
        "DISCOVERYLAND":   "#0ea5e9",
        "AVENGERS CAMPUS": "#dc2626",
        "WORLD OF PIXAR":  "#2563eb",
        "PRODUCTION 3":    "#ca8a04",
        "WORLD OF FROZEN": "#06b6d4",
        "ADVENTURE WAY":   "#059669",
    }

    LAND_COLORS_LIGHT = {
        "MAINSTREET":      "#fcd34d",
        "FRONTIERLAND":    "#fb923c",
        "ADVENTURELAND":   "#4ade80",
        "FANTASYLAND":     "#c084fc",
        "DISCOVERYLAND":   "#38bdf8",
        "AVENGERS CAMPUS": "#f87171",
        "WORLD OF PIXAR":  "#60a5fa",
        "PRODUCTION 3":    "#fde047",
        "WORLD OF FROZEN": "#67e8f9",
        "ADVENTURE WAY":   "#34d399",
    }

    PARC_COLORS = {
        "Disneyland Park":        "#ffb3d1",
        "Disney Adventure World": "#fb923c",
    }

    def load_df(date_from, date_to=None):
        try:
            q = supabase.table("logs_101").select("*").gte("start_time", date_from.isoformat())
            if date_to:
                q = q.lt("start_time", date_to.isoformat())
            resp = q.execute()
            df = pd.DataFrame(resp.data)
            if df.empty: return df
            df = df.copy()
            df['start_dt'] = pd.to_datetime(df['start_time']).dt.tz_convert('Europe/Paris')
            df['end_dt']   = df['end_time'].apply(
                lambda x: pd.to_datetime(x).tz_convert('Europe/Paris') if pd.notna(x) else pd.Timestamp.now(tz='Europe/Paris')
            )
            df['duree_min'] = (df['end_dt'] - df['start_dt']).dt.total_seconds() / 60
            df = df[df['duree_min'] >= 5]
            df = df[df['duree_min'] <= 420]
            df = df[~df['ride_name'].isin(STATS_EXCLUDED)]
            df = df[~df.apply(is_during_rehab, axis=1)]
            r2p, r2l = {}, {}
            for park, lands in PARKS_DATA.items():
                for land, attractions in lands.items():
                    for attr in attractions:
                        r2p[attr] = park
                        r2l[attr] = land
            df['parc'] = df['ride_name'].map(r2p).fillna("Inconnu")
            df['land'] = df['ride_name'].map(r2l).fillna("Inconnu")
            return df
        except Exception as e:
            st.error(f"Erreur stats : {e}")
            return pd.DataFrame()

    df_mois    = load_df(debut_mois)
    df_mois_pr = load_df(debut_mois_pr, fin_mois_pr)

    ride_to_park = {}
    ride_to_land = {}
    for park, lands in PARKS_DATA.items():
        for land, attractions in lands.items():
            for attr in attractions:
                ride_to_park[attr] = park
                ride_to_land[attr] = land

    def stats_block(df):
        nb    = len(df)
        total = int(df['duree_min'].sum()) if nb > 0 else 0
        moy   = int(df['duree_min'].mean()) if nb > 0 else 0
        return nb, total, moy

    def badge(value, label, color):
        return (
            '<span style="display:inline-flex; flex-direction:column; align-items:center;'
            'background:' + color + '18; border:1px solid ' + color + '35;'
            'border-radius:10px; padding:5px 11px; margin:2px;">'
            '<span style="font-family:Outfit,sans-serif; font-size:15px; font-weight:800; color:' + color + '; line-height:1;">' + str(value) + '</span>'
            '<span style="font-size:7.5px; color:' + color + '90; font-weight:600; text-transform:uppercase; letter-spacing:0.8px; margin-top:2px;">' + label + '</span>'
            '</span>'
        )

    def badge_sm(value, label, color):
        return (
            '<span style="display:inline-flex; flex-direction:column; align-items:center;'
            'background:' + color + '12; border:1px solid ' + color + '28;'
            'border-radius:8px; padding:3px 8px; margin:2px;">'
            '<span style="font-family:Outfit,sans-serif; font-size:12px; font-weight:800; color:' + color + '99; line-height:1;">' + str(value) + '</span>'
            '<span style="font-size:6.5px; color:' + color + '60; font-weight:600; text-transform:uppercase; letter-spacing:0.8px; margin-top:2px;">' + label + '</span>'
            '</span>'
        )

    def prev_block(df_pr, c_int="#64748b", c_min="#64748b", c_moy="#64748b"):
        if df_pr is None or df_pr.empty: return ""
        nb, total, moy = stats_block(df_pr)
        return (
            '<div style="margin-top:8px; padding:6px 6px;'
            'background:rgba(255,255,255,0.015); border:1px solid rgba(255,255,255,0.05);'
            'border-radius:8px; opacity:0.5;">'
            '<span style="font-size:7px; color:#475569; font-weight:700;'
            'text-transform:uppercase; letter-spacing:1px;">📅 ' + mois_pr_label + ' — </span>'
            + badge_sm(nb, "Interruptions", c_int)
            + badge_sm(total, "Min Total", c_min)
            + badge_sm(moy, "Min Moyenne", c_moy)
            + '</div>'
        )

    def detail_expander(df_sub, label, color_l):
        with st.expander(f"📋 {label}"):
            for _, row in df_sub.sort_values('start_dt', ascending=False).iterrows():
                debut     = row['start_dt'].strftime('%d/%m %H:%M')
                fin       = row['end_dt'].strftime('%H:%M') if pd.notna(row['end_time']) else "En cours"
                duree     = int(row['duree_min'])
                fin_color = "#f87171" if fin == "En cours" else "#94a3b8"
                rname     = row['ride_name']
                st.markdown(
                    '<div style="display:flex; justify-content:space-between; align-items:center;'
                    'padding:5px 8px; background:rgba(255,255,255,0.02); border-radius:7px; margin-bottom:3px;">'
                    '<div style="display:flex; align-items:center; gap:6px;">'
                    '<span style="font-size:13px;">' + get_emoji(rname) + '</span>'
                    '<div>'
                    '<span style="color:rgba(255,255,255,0.65); font-size:10px; font-weight:500; display:block;">' + rname + '</span>'
                    '<span style="color:#475569; font-size:9px;">' + debut + ' → <span style="color:' + fin_color + ';">' + fin + '</span></span>'
                    '</div></div>'
                    '<span style="font-family:Outfit,sans-serif; font-size:10px; font-weight:700;'
                    'color:' + color_l + '; background:' + color_l + '15; border:1px solid ' + color_l + '30;'
                    'padding:1px 7px; border-radius:6px;">' + str(duree) + ' min</span>'
                    '</div>',
                    unsafe_allow_html=True
                )

    if df_mois.empty:
        st.caption("Pas d'interruptions ce mois-ci.")
    else:
        nb_g, total_g, moy_g = stats_block(df_mois)


        # === RÉSUMÉ GLOBAL ===
        st.markdown(
            '<div style="display:flex; gap:6px; flex-wrap:wrap; margin-bottom:6px;">'
            + badge(nb_g, "Interruptions", "#c4b5fd")
            + badge(total_g, "Min Total", "#7dd3fc")
            + badge(moy_g, "Min Moyenne", "#6ee7b7")
            + '</div>',
            unsafe_allow_html=True
        )

        # Mois précédent global
        if not df_mois_pr.empty:
            nb_pr, total_pr, moy_pr = stats_block(df_mois_pr)
            st.markdown(
                '<div style="display:flex; align-items:center; gap:4px; flex-wrap:wrap; margin-bottom:14px;'
                'padding:6px 10px; background:rgba(255,255,255,0.015); border:1px solid rgba(255,255,255,0.05);'
                'border-radius:10px; opacity:0.6;">'
                '<span style="font-size:7.5px; color:#475569; font-weight:700; text-transform:uppercase;'
                'letter-spacing:1px; margin-right:2px;">📅 ' + mois_pr_label + ' —</span>'
                + badge_sm(nb_pr, "Interruptions", "#c4b5fd")
                + badge_sm(total_pr, "Min Total", "#7dd3fc")
                + badge_sm(moy_pr, "Min Moyenne", "#6ee7b7")
                + '</div>',
                unsafe_allow_html=True
            )

        # === PAR PARC ===
        with st.expander("🏰 Par parc", expanded=True):
            for parc_name, parc_label in [
                ("Disneyland Park",        "🏰 Disneyland Park"),
                ("Disney Adventure World", "🎬 Disney Adventure World"),
            ]:
                parc_color = PARC_COLORS[parc_name]
                df_p       = df_mois[df_mois['parc'] == parc_name]
                df_p_pr    = df_mois_pr[df_mois_pr['parc'] == parc_name] if not df_mois_pr.empty else pd.DataFrame()
                if df_p.empty: continue

                nb_p, total_p, moy_p = stats_block(df_p)

                lands_html = ""
                for land, attractions in PARKS_DATA[parc_name].items():
                    df_l    = df_p[df_p['land'] == land]
                    df_l_pr = df_p_pr[df_p_pr['land'] == land] if not df_p_pr.empty else pd.DataFrame()
                    if df_l.empty: continue
                    color   = LAND_COLORS.get(land, "#64748b")
                    color_l = LAND_COLORS_LIGHT.get(land, "#94a3b8")
                    nb_l, total_l, moy_l = stats_block(df_l)

                    rides_html = ""
                    for attr_name in attractions:
                        df_r    = df_mois[df_mois['ride_name'] == attr_name]
                        df_r_pr = df_mois_pr[df_mois_pr['ride_name'] == attr_name] if not df_mois_pr.empty else pd.DataFrame()
                        df_a = df_l[df_l['ride_name'] == attr_name]
                        if df_a.empty: continue
                        nb_a, total_a, moy_a = stats_block(df_a)
                        rides_html += (
                            '<div style="display:flex; align-items:center; gap:6px; flex-wrap:wrap;'
                            'padding:5px 8px; background:' + color + '06;'
                            'border:1px solid ' + color + '12; border-radius:8px; margin-bottom:3px;">'
                            '<span style="font-size:13px; flex-shrink:0;">' + get_emoji(attr_name) + '</span>'
                            '<span style="font-family:Mulish,sans-serif; color:rgba(255,255,255,0.65);'
                            'font-size:10px; font-weight:600; flex:1; min-width:0; word-break:break-word;">' + attr_name + '</span>'
                            '<div style="display:flex; gap:3px; flex-shrink:0;">'
                            + badge_sm(nb_a, "Interruptions", color)
                            + badge_sm(total_a, "Min Total", color_l)
                            + badge_sm(moy_a, "Min Moyenne", color_l)
                            + '</div>'
                            + prev_block(df_r_pr, color, color_l, color_l)
                            + '</div>'
                        )

                    lands_html += (
                        '<div style="padding:8px 10px; background:' + color + '08;'
                        'border:1px solid ' + color + '28; border-left:3px solid ' + color + ';'
                        'border-radius:10px; margin-bottom:5px;">'
                        '<div style="font-family:Outfit,sans-serif; font-size:9px; font-weight:700;'
                        'color:' + color + '; text-transform:uppercase; letter-spacing:1px; margin-bottom:5px;">'
                        + land.title() + '</div>'
                        '<div style="display:flex; gap:4px; flex-wrap:wrap; margin-bottom:' + ('6px' if rides_html else '0') + ';">'
                        + badge_sm(nb_l, "Interruptions", color)
                        + badge_sm(total_l, "Min Total", color_l)
                        + badge_sm(moy_l, "Min Moyenne", color_l)
                        + prev_block(df_l_pr, color, color_l, color_l)
                        + '</div>'
                        + rides_html
                        + '</div>'
                    )

                prev_parc_html = prev_block(df_p_pr, parc_color, parc_color, parc_color)

                st.markdown(
                    '<div style="padding:13px 14px; background:' + parc_color + '06;'
                    'border:2px solid ' + parc_color + '35; border-radius:16px; margin-bottom:10px;">'
                    '<div style="font-family:Outfit,sans-serif; font-size:11px; font-weight:700;'
                    'color:' + parc_color + '; margin-bottom:8px;">' + parc_label + '</div>'
                    '<div style="display:flex; gap:5px; flex-wrap:wrap; margin-bottom:10px;">'
                    + badge(nb_p, "Interruptions", parc_color)
                    + badge(total_p, "Min Total", parc_color)
                    + badge(moy_p, "Min Moyenne", parc_color)
                    + prev_parc_html
                    + '</div>'
                    + lands_html
                    + '</div>',
                    unsafe_allow_html=True
                )

        # === PAR LAND ===
        with st.expander("🗺️ Par land"):
            all_lands       = [l for lands in PARKS_DATA.values() for l in lands.keys()]
            available_lands = [l for l in all_lands if not df_mois[df_mois['land'] == l].empty]
            selected_lands  = st.multiselect("", options=available_lands,
                default=available_lands[:1] if available_lands else [], key="stats_lands")
            for land in selected_lands:
                color   = LAND_COLORS.get(land, "#64748b")
                color_l = LAND_COLORS_LIGHT.get(land, "#94a3b8")
                df_l    = df_mois[df_mois['land'] == land]
                df_l_pr = df_mois_pr[df_mois_pr['land'] == land] if not df_mois_pr.empty else pd.DataFrame()
                nb, total, moy = stats_block(df_l)

                attractions_du_land = [
                    a for p_lands in PARKS_DATA.values()
                    for l, attrs in p_lands.items()
                    if l == land for a in attrs
                ]
                rows_html = ""
                for attr_name in attractions_du_land:
                    df_r    = df_mois[df_mois['ride_name'] == attr_name]
                    df_r_pr = df_mois_pr[df_mois_pr['ride_name'] == attr_name] if not df_mois_pr.empty else pd.DataFrame()
                    df_a = df_l[df_l['ride_name'] == attr_name]
                    if df_a.empty: continue
                    nb_a, total_a, moy_a = stats_block(df_a)
                    rows_html += (
                        '<div style="display:flex; align-items:center; gap:6px; flex-wrap:wrap;'
                        'padding:5px 8px; background:' + color + '06;'
                        'border:1px solid ' + color + '12; border-radius:8px; margin-bottom:3px;">'
                        '<span style="font-size:13px; flex-shrink:0;">' + get_emoji(attr_name) + '</span>'
                        '<span style="font-family:Mulish,sans-serif; color:rgba(255,255,255,0.65);'
                        'font-size:10px; font-weight:600; flex:1; min-width:0; word-break:break-word;">' + attr_name + '</span>'
                        '<div style="display:flex; gap:3px; flex-shrink:0;">'
                        + badge_sm(nb_a, "Interruptions", color)
                        + badge_sm(total_a, "Min Total", color_l)
                        + badge_sm(moy_a, "Min Moyenne", color_l)
                        + '</div>'
                        + prev_block(df_r_pr, color, color_l, color_l)
                        + '</div>'
                    )

                st.markdown(
                    '<div style="padding:10px 14px; background:' + color + '08;'
                    'border:1px solid ' + color + '25; border-left:3px solid ' + color + ';'
                    'border-radius:12px; margin-bottom:8px;">'
                    '<div style="font-family:Outfit,sans-serif; font-size:10px; font-weight:700;'
                    'color:' + color + '; text-transform:uppercase; letter-spacing:1px; margin-bottom:8px;">'
                    + land.title() + '</div>'
                    '<div style="display:flex; gap:6px; flex-wrap:wrap; margin-bottom:' + ('10px' if rows_html else '0') + ';">'
                    + badge(nb, "Interruptions", color)
                    + badge(total, "Min Total", color_l)
                    + badge(moy, "Min Moyenne", color_l)
                    + prev_block(df_l_pr, color, color_l, color_l)
                    + '</div>'
                    + (('<div style="margin-top:8px;">' + rows_html + '</div>') if rows_html else '')
                    + '</div>',
                    unsafe_allow_html=True
                )
                detail_expander(df_l, f"Détail — {land.title()}", color_l)

        # === PAR ATTRACTION ===
        with st.expander("🎢 Par attraction"):
            available_rides = (df_mois.groupby('ride_name')['duree_min'].count()
                               .sort_values(ascending=False).index.tolist())
            selected_rides  = st.multiselect("", options=available_rides,
                default=available_rides[:1] if available_rides else [],
                format_func=lambda x: f"{get_emoji(x)} {x}", key="stats_rides")
            for ride in selected_rides:
                land    = ride_to_land.get(ride, "Inconnu")
                color   = LAND_COLORS.get(land, "#64748b")
                color_l = LAND_COLORS_LIGHT.get(land, "#94a3b8")
                df_r    = df_mois[df_mois['ride_name'] == ride]
                df_r_pr = df_mois_pr[df_mois_pr['ride_name'] == ride] if not df_mois_pr.empty else pd.DataFrame()
                nb, total, moy = stats_block(df_r)
                st.markdown(
                    '<div style="padding:10px 14px; background:' + color + '06;'
                    'border:1px solid ' + color + '20; border-left:3px solid ' + color_l + ';'
                    'border-radius:12px; margin-bottom:4px;">'
                    '<div style="display:flex; align-items:center; gap:8px; margin-bottom:4px;">'
                    '<span style="font-size:18px;">' + get_emoji(ride) + '</span>'
                    '<span style="font-family:Outfit,sans-serif; color:rgba(255,255,255,0.8);'
                    'font-size:12px; font-weight:600;">' + ride + '</span>'
                    '</div>'
                    '<div style="margin-bottom:8px; margin-left:26px;">'
                    '<span style="font-size:9px; font-weight:700; padding:2px 9px; border-radius:20px;'
                    'background:' + color + '20; color:' + color + '; border:1px solid ' + color + '40;'
                    'font-family:Outfit,sans-serif; text-transform:uppercase; letter-spacing:0.8px;">'
                    + land.title() + '</span>'
                    '</div>'
                    '<div style="display:flex; gap:6px; flex-wrap:wrap;">'
                    + badge(nb, "Interruptions", color)
                    + badge(total, "Min Total", color_l)
                    + badge(moy, "Min Moyenne", color_l)
                    + prev_block(df_r_pr, color, color_l, color_l)
                    + '</div>'
                    + '</div>',
                    unsafe_allow_html=True
                )
                detail_expander(df_r, f"Détail — {ride}", color_l)

st.divider()
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