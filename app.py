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
st.set_page_config(page_title="Disney Live Control", page_icon="🏰", layout="centered")

# --- CONNEXION SUPABASE ---
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

# --- ACTUALISATION AUTOMATIQUE (60 secondes) ---
st_autorefresh(interval=60000, key="datarefresh")

# Stockage de l'heure du dernier refresh
paris_tz = pytz.timezone('Europe/Paris')
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = datetime.now(paris_tz).strftime("%H:%M:%S")
else:
    st.session_state.last_refresh = datetime.now(paris_tz).strftime("%H:%M:%S")

# --- FONCTION POUR GITHUB ---
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

# --- LOGIQUE DE RESET À 02:00 DU MATIN ---
# On définit l'heure charnière à 2h00
heure_reset = maintenant.replace(hour=2, minute=0, second=0, microsecond=0)
# Si il est moins de 2h du matin, le reset a eu lieu hier à 2h
if maintenant < heure_reset:
    debut_journee = heure_reset - timedelta(days=1)
else:
    debut_journee = heure_reset

if st.button('🔄 Actualiser & Forcer un Relevé'):
    with st.spinner("Signal envoyé au robot..."):
        if trigger_github_action() == 204:
            st.toast("🚀 Robot lancé !"); time.sleep(45); st.rerun()

# --- RÉCUPÉRATION DES DONNÉES (Depuis 2h du matin) ---
try:
    response = supabase.table("disney_logs") \
        .select("*") \
        .gte("created_at", debut_journee.isoformat()) \
        .order("created_at", desc=False) \
        .execute()
    df_raw = pd.DataFrame(response.data)
except:
    df_raw = pd.DataFrame()

if not df_raw.empty:
    df_raw['created_at'] = pd.to_datetime(df_raw['created_at']).dt.tz_convert('Europe/Paris')
    
    # --- FILTRAGE : Exclure maintenance (2h -> 8h) ---
    df = df_raw[~((df_raw['created_at'].dt.hour >= 2) & (df_raw['created_at'].dt.hour < 8))].copy()
    
    if not df.empty:
        derniere_maj = df['created_at'].max().strftime("%H:%M:%S")

        # --- CALCUL GLOBAL DES PANNES ---
        all_pannes = []
        toutes_attractions = sorted(df['ride_name'].unique())
        
        for ride_name in toutes_attractions:
            ride_data = df[df['ride_name'] == ride_name].sort_values('created_at')
            en_panne, debut_panne = False, None
            for i, row in ride_data.iterrows():
                if not row['is_open'] and not en_panne:
                    en_panne, debut_panne = True, row['created_at']
                elif row['is_open'] and en_panne:
                    all_pannes.append({
                        "ride": ride_name, "debut": debut_panne, "fin": row['created_at'],
                        "duree": int((row['created_at'] - debut_panne).total_seconds() / 60),
                        "statut": "TERMINEE"
                    })
                    en_panne = False
            if en_panne:
                all_pannes.append({"ride": ride_name, "debut": debut_panne, "fin": None, "statut": "EN_COURS"})

        # --- LOGIQUE RACCOURCIS ---
        st.write("---")
        sc = st.text_input("Raccourci : `*DLP`, `*FANTASY`, `*CAMPUS`, `*FROZEN`...", placeholder="Tape ici...")
        
        current_selection = st.query_params.get_all("fav")
        if sc == "*101":
            current_selection = [p['ride'] for p in all_pannes if p['statut'] == "EN_COURS"]
        elif sc == "*102":
            current_selection = list(set([p['ride'] for p in all_pannes]))
        elif sc.startswith("*"):
            shortcut_selection = get_rides_by_zone(sc, toutes_attractions)
            if shortcut_selection: current_selection = shortcut_selection

        selected_options = st.multiselect("Attractions suivies :", options=toutes_attractions, default=current_selection, format_func=lambda x: f"{get_emoji(x)} {x}")
        st.query_params["fav"] = selected_options
        
        st.caption(f"🕒 Donnée : {derniere_maj} | Auto-refresh : {st.session_state.last_refresh} (60s)")
        
        # --- AFFICHAGE ---
        if not selected_options:
            st.info(f"👆 Sélectionne des attractions. (Données reset à {debut_journee.strftime('%H:%M')})")
            st.divider()

        
        else:
            st.divider()
            for ride in selected_options:
                ride_df = df[df['ride_name'] == ride].sort_values('created_at', ascending=False)
                if not ride_df.empty:
                    last = ride_df.iloc[0]
                    st.subheader(f"{get_emoji(ride)} {ride}")
                    
                    c1, c2 = st.columns(2)
                    if last['is_open']:
                        c1.success("🟢 OUVERT")
                        c2.metric("Attente", f"{int(last['wait_time'])} min")
                    else:
                        c1.error("🔴 FERMÉ / PANNE")
                        c2.metric("Attente", "- - -")

                    ride_pannes = [p for p in all_pannes if p['ride'] == ride]
                    panne_actuelle = next((p for p in ride_pannes if p['statut'] == "EN_COURS"), None)
                    if panne_actuelle:
                        min_e = int((maintenant - panne_actuelle['debut']).total_seconds() / 60)
                        st.warning(f"⚠️ Down depuis {min_e} min (à {panne_actuelle['debut'].strftime('%H:%M')})")

                    with st.expander("📜 Historique des pannes du jour"):
                        if ride_pannes:
                            for p in reversed(ride_pannes):
                                if p['statut'] == "TERMINEE":
                                    st.write(f"• Panne de {p['debut'].strftime('%H:%M')} à {p['fin'].strftime('%H:%M')} ({p['duree']} min)")
                                else:
                                    diff = int((maintenant - p['debut']).total_seconds() / 60)
                                    st.write(f"• ⚠️ **En cours** : depuis {p['debut'].strftime('%H:%M')} ({diff} min)")
                        else:
                            st.write("✅ Pas de panne détectée aujourd'hui")
                    st.divider()

        # --- FLUX GLOBAL ---
        st.subheader("🚨 Flux des dernières pannes du parc")
        flux = sorted(all_pannes, key=lambda x: x['debut'], reverse=True)[:5]
        if flux:
            for p in flux:
                if p['statut'] == "EN_COURS": st.error(f"🔴 **{p['ride']}** en panne à {p['debut'].strftime('%H:%M')}")
                else: st.info(f"✅ **{p['ride']}** rouvert à {p['fin'].strftime('%H:%M')} ({p['duree']} min)")
        else: st.write("✅ Aucune panne enregistrée aujourd'hui.")
    else:
        st.warning(f"😴 Le parc est en maintenance. (Dernier reset à {debut_journee.strftime('%H:%M')})")

else:
    st.warning("📭 Aucune donnée disponible pour aujourd'hui.")

st.markdown("<style>[data-testid='stMetricValue'] { font-size: 1.8rem; } .stButton button { width: 100%; border-radius: 10px; }</style>", unsafe_allow_html=True)
