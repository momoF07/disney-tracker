import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime, timedelta
import pytz
import requests
import time
from streamlit_autorefresh import st_autorefresh 
from emojis import get_emoji

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
st.session_state.last_refresh = datetime.now(paris_tz).strftime("%H:%M:%S")

# --- FONCTION POUR DÉCLENCHER LE ROBOT ---
def trigger_github_action():
    REPO = "momoF07/disney-tracker"
    WORKFLOW_ID = "check.yml"
    TOKEN = st.secrets["GITHUB_TOKEN"]
    url = f"https://api.github.com/repos/{REPO}/actions/workflows/{WORKFLOW_ID}/dispatches"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    try:
        res = requests.post(url, headers=headers, json={"ref": "main"})
        return res.status_code
    except:
        return 500

# --- INTERFACE ---
st.title("🏰 Disney Wait Time")

maintenant = datetime.now(paris_tz)

# Logique de Reset à 02:00 du matin
heure_reset = maintenant.replace(hour=2, minute=0, second=0, microsecond=0)
if maintenant < heure_reset:
    debut_journee = heure_reset - timedelta(days=1)
else:
    debut_journee = heure_reset

if st.button('🔄 Actualiser & Forcer un Relevé'):
    with st.spinner("Signal envoyé au robot..."):
        status = trigger_github_action()
        if status == 204:
            st.toast("🚀 Robot lancé ! Attente des données...")
            time.sleep(45)
            st.rerun()
        else:
            st.error("Erreur lors du lancement du robot.")

# --- RÉCUPÉRATION DES DONNÉES (Depuis 2h du matin) ---
try:
    response = supabase.table("disney_logs") \
        .select("*") \
        .gte("created_at", debut_journee.isoformat()) \
        .order("created_at", desc=False) \
        .execute()
    df_raw = pd.DataFrame(response.data)
except Exception as e:
    st.error(f"Erreur de connexion : {e}")
    df_raw = pd.DataFrame()

if not df_raw.empty:
    # Conversion des dates
    df_raw['created_at'] = pd.to_datetime(df_raw['created_at']).dt.tz_convert('Europe/Paris')
    
    # Filtrage : Exclure maintenance nocturne (2h -> 8h)
    df = df_raw[~((df_raw['created_at'].dt.hour >= 2) & (df_raw['created_at'].dt.hour < 8))].copy()
    
    if not df.empty:
        derniere_maj = df['created_at'].max().strftime("%H:%M:%S")
        toutes_attractions = sorted(df['ride_name'].unique())
        
        # --- CALCUL DES PANNES ---
        all_pannes = []
        for ride_name in toutes_attractions:
            ride_data = df[df['ride_name'] == ride_name].sort_values('created_at')
            en_panne = False
            debut_panne = None
            
            for i, row in ride_data.iterrows():
                if not row['is_open'] and not en_panne:
                    en_panne = True
                    debut_panne = row['created_at']
                elif row['is_open'] and en_panne:
                    all_pannes.append({
                        "ride": ride_name,
                        "debut": debut_panne,
                        "fin": row['created_at'],
                        "duree": int((row['created_at'] - debut_panne).total_seconds() / 60),
                        "statut": "TERMINEE"
                    })
                    en_panne = False
            
            if en_panne:
                all_pannes.append({
                    "ride": ride_name,
                    "debut": debut_panne,
                    "fin": None,
                    "statut": "EN_COURS"
                })

        # --- FILTRE ET SÉLECTION ---
        selected_options = st.multiselect(
            "Sélectionne des attractions :",
            options=toutes_attractions,
            default=st.query_params.get_all("fav"),
            format_func=lambda x: f"{get_emoji(x)} {x}"
        )
        st.query_params["fav"] = selected_options

        st.caption(f"🕒 Dernière donnée : {derniere_maj} | Auto-refresh : {st.session_state.last_refresh} (60s)")

        # --- AFFICHAGE DES ATTRACTIONS ---
        if not selected_options:
            st.info("Sélectionne des attractions pour voir les temps d'attente.")
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

                    # Affichage panne actuelle
                    ride_pannes = [p for p in all_pannes if p['ride'] == ride]
                    panne_actuelle = next((p for p in ride_pannes if p['statut'] == "EN_COURS"), None)
                    if panne_actuelle:
                        duree_actuelle = int((maintenant - panne_actuelle['debut']).total_seconds() / 60)
                        st.warning(f"⚠️ En panne depuis {duree_actuelle} min (début à {panne_actuelle['debut'].strftime('%H:%M')})")

                    # Historique
                    with st.expander("Historique des pannes aujourd'hui"):
                        if ride_pannes:
                            for p in reversed(ride_pannes):
                                if p['statut'] == "TERMINEE":
                                    st.write(f"• De {p['debut'].strftime('%H:%M')} à {p['fin'].strftime('%H:%M')} ({p['duree']} min)")
                                else:
                                    st.write(f"• ⚠️ En cours depuis {p['debut'].strftime('%H:%M')}")
                        else:
                            st.write("✅ Aucune panne détectée aujourd'hui.")
                    st.divider()

        # --- FLUX DES DERNIÈRES PANNES ---
        st.subheader("🚨 Flux des dernières pannes")
        flux_pannes = sorted(all_pannes, key=lambda x: x['debut'], reverse=True)[:5]
        if flux_pannes:
            for p in flux_pannes:
                if p['statut'] == "EN_COURS":
                    st.error(f"🔴 **{p['ride']}** est tombé en panne à {p['debut'].strftime('%H:%M')}")
                else:
                    st.info(f"✅ **{p['ride']}** a rouvert à {p['fin'].strftime('%H:%M')} (durée : {p['duree']} min)")
        else:
            st.write("Aucune panne enregistrée aujourd'hui.")

    else:
        st.warning("Le parc est actuellement fermé ou en maintenance (relevés entre 08:00 et 02:00).")
else:
    st.warning("Aucune donnée disponible pour le moment.")

# Style pour les cartes
st.markdown("""
<style>
[data-testid="stMetricValue"] { font-size: 1.8rem; }
.stButton button { width: 100%; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)
