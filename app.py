import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime, timedelta
import pytz
import requests
import time
from streamlit_autorefresh import st_autorefresh 
from emojis import get_emoji 
import altair as alt # <-- Nouvel import indispensable

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Disney Live Dashboard", page_icon="🏰", layout="centered")

# --- CONNEXION SUPABASE ---
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

# --- ACTUALISATION AUTOMATIQUE (60 secondes) ---
st_autorefresh(interval=60000, key="datarefresh")

# --- FONCTION POUR DÉCLENCHER LE ROBOT GITHUB ---
def trigger_github_action():
    REPO = "momoF07/disney-tracker" 
    WORKFLOW_ID = "check.yml"
    TOKEN = st.secrets["GITHUB_TOKEN"]
    url = f"https://api.github.com/repos/{REPO}/actions/workflows/{WORKFLOW_ID}/dispatches"
    headers = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        res = requests.post(url, headers=headers, json={"ref": "main"})
        return res.status_code
    except: return 500

# --- INTERFACE ---
st.title("🏰 My Disney Dashboard")

paris_tz = pytz.timezone('Europe/Paris')
maintenant = datetime.now(paris_tz)
aujourd_hui = maintenant.strftime("%Y-%m-%d")

if st.button('🔄 Forcer un relevé maintenant'):
    with st.spinner("Le robot analyse les parcs..."):
        status = trigger_github_action()
        if status == 204:
            st.toast("🚀 Robot lancé !", icon="✅")
            time.sleep(40) 
            st.rerun()

# Récupération des données Disney (Garde les 24 dernières heures pour le graphique)
try:
    hier_a_cette_heure = maintenant - timedelta(hours=24)
    response = supabase.table("disney_logs") \
        .select("*") \
        .gte("created_at", hier_a_cette_heure.isoformat()) \
        .order("created_at", desc=True) \
        .execute()
    df = pd.DataFrame(response.data)
except:
    df = pd.DataFrame()

if not df.empty:
    df['created_at'] = pd.to_datetime(df['created_at']).dt.tz_convert('Europe/Paris')
    derniere_maj = df['created_at'].max().strftime("%H:%M:%S")
    
    toutes_attractions = sorted(df['ride_name'].unique())
    
    # Favoris (Stockés dans l'URL)
    st.write("**Favoris (Stockés dans l'URL)**")
    params = st.query_params.get_all("fav")
    selected_options = st.multiselect(
        "Sélectionne tes attractions préférées :",
        options=toutes_attractions,
        default=params,
        format_func=lambda x: f"{get_emoji(x)} {x}",
        placeholder="Rechercher une attraction...",
        key="favoris"
    )
    st.query_params["fav"] = selected_options

    st.caption(f"⏱️ Auto-refresh : {maintenant.strftime('%H:%M:%S')} | 🕒 Data : {derniere_maj}")
    st.divider()

    # --- BOUCLE D'AFFICHAGE DES FAVORIS ---
    if not selected_options:
        st.info("👆 Sélectionne tes attractions pour les suivre en direct.")
    else:
        for ride in selected_options:
            ride_df = df[df['ride_name'] == ride].sort_values('created_at', ascending=False)
            if not ride_df.empty:
                last = ride_df.iloc[0]
                
                st.subheader(f"{get_emoji(ride)} {ride}")
                
                c1, c2 = st.columns(2)
                wait = last['wait_time']
                is_open = last['is_open']
                
                if is_open:
                    c1.success("🟢 OUVERT")
                    
                    # Choix de la couleur de l'émoji pour le titre du graphique
                    color_emoji = "🟢 Vert" if wait <= 25 else "🟠 Orange" if wait <= 55 else "🔴 Rouge"
                    c2.metric("Attente", f"{int(wait)} min")
                else:
                    c1.error("🔴 FERMÉ / PANNE")
                    c2.metric("Attente", "- - -")
                
                # Gestion détaillée des pannes
                if not is_open:
                    ride_chrono = ride_df.sort_values('created_at')
                    last_open = ride_chrono[ride_chrono['is_open'] == True].last_valid_index()
                    if last_open is not None:
                        start_panne = ride_chrono.loc[last_open + 1:].iloc[0]['created_at']
                        diff = maintenant - start_panne
                        h, r = divmod(diff.total_seconds(), 3600)
                        m, _ = divmod(r, 60)
                        txt = f"{int(m)}min" if h == 0 else f"{int(h)}h{int(m)}min"
                        st.warning(f"⚠️ En panne depuis {txt} (à {start_panne.strftime('%H:%M')})")
                
                # --- GRAPHIQUE EN DÉGRADÉ (DÉLIRANT ET CORRIGÉ) ---
                # Ne générer le graphique que s'il y a assez de données
                if len(ride_df) > 1 and is_open:
                    st.caption(f"Evolution de l'attente ({int(wait)} min - {color_emoji})")
                    
                    # On ne garde que les 4 dernières heures pour plus de lisibilité
                    four_hours_ago = maintenant - timedelta(hours=4)
                    chart_data = ride_df[ride_df['created_at'] >= four_hours_ago].copy()
                    
                    # Nettoyage des données pour le dégradé
                    chart_data['wait_time'] = chart_data['wait_time'].fillna(0)

                    # 1. Définir le dégradé vertical basé sur les seuils réels
                    # L'échelle Y est fixée de 0 à 80 pour la cohérence.
                    gradient = alt.Gradient(
                        gradient='linear',
                        stops=[
                            # Zone Verte Fluide (0-25 min)
                            alt.GradientStop(color='green', offset=0),       # 0 min
                            alt.GradientStop(color='green', offset=25/80),   # 25 min (Vert pur)
                            
                            # Zone Orange Modérée (30-55 min)
                            alt.GradientStop(color='orange', offset=30/80),  # 30 min (Début orange pur)
                            alt.GradientStop(color='orange', offset=55/80),  # 55 min (Fin orange pur)
                            
                            # Zone Rouge Saturée (60+ min)
                            alt.GradientStop(color='red', offset=60/80),     # 60 min (Début rouge pur)
                            alt.GradientStop(color='red', offset=1)          # 80 min (Rouge pur, maximum)
                        ],
                        x1=1, x2=1, y1=1, y2=0 # Dégradé vertical (y-axis)
                    )

                    # 2. Construction de la base du graphique
                    base = alt.Chart(chart_data).encode(
                        x=alt.X('created_at:T', title="Heure", axis=alt.Axis(format="%H:%M")),
                        y=alt.Y('wait_time:Q', title="Temps d'attente (Min)", scale=alt.Scale(domain=[0, 80])),
                        tooltip=[alt.Tooltip('created_at:T', format="%H:%M"), alt.Tooltip('wait_time:Q', title="Min")]
                    )

                    # 3. Création de l'aire remplie avec le dégradé correct
                    # J'ai supprimé les aires empilées plates.
                    area = base.mark_area(
                        color=gradient,
                        line=False # On utilise la ligne séparée pour le contour
                    )

                    # 4. Création de la ligne de données unie (conserver le style bleu)
                    line = base.mark_line(color='#1f77b4', size=2)

                    # 5. Combiner l'aire dégradée et la ligne de contour
                    final_chart = (area + line).properties(
                        height=250 # Hauteur fixe pour mobile
                    ).configure_view(
                        strokeOpacity=0 # Supprimer le cadre du graphique
                    ).configure_legend(
                        disable=True # Supprimer toute légende générée automatiquement
                    ).interactive(False) # DÉZOOOM/BOUGER SOURIS DÉSACTIVÉ

                    st.altair_chart(final_chart, use_container_width=True)

                st.divider()
else:
    st.warning("📭 Aucune donnée disponible aujourd'hui.")

# CSS (Métrics plus gros, Bouton 100% largeur)
st.markdown("""
    <style>
    [data-testid='stMetricValue'] { font-size: 1.8rem; } 
    .stButton button { width: 100%; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)
