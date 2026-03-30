import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
import pytz
import altair as alt

# Config de la page
st.set_page_config(page_title="Disney Live Tracker", page_icon="🎢", layout="wide")

# Connexion Supabase
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

# --- GESTION DU TEMPS ---
paris_tz = pytz.timezone('Europe/Paris')
maintenant = datetime.now(paris_tz)
aujourd_hui = maintenant.strftime("%Y-%m-%d")

st.title("🎢 Suivi en Direct - Disneyland Paris")
st.caption(f"Données du jour : {maintenant.strftime('%d/%m/%Y')}")

# --- 1. RÉCUPÉRATION DES DONNÉES DU JOUR UNIQUEMENT ---
try:
    response = supabase.table("disney_logs") \
        .select("*") \
        .gte("created_at", f"{aujourd_hui}T00:00:00") \
        .order("created_at", desc=True) \
        .execute()
    
    df = pd.DataFrame(response.data)
except Exception as e:
    st.error(f"Erreur de connexion : {e}")
    df = pd.DataFrame()

if not df.empty:
    # Conversion du temps et tri
    df['created_at'] = pd.to_datetime(df['created_at']).dt.tz_convert('Europe/Paris')
    
    # --- AFFICHAGE DE LA DERNIÈRE MAJ ---
    derniere_maj = df['created_at'].max().strftime("%H:%M:%S")
    st.info(f"🕒 Dernière actualisation du robot : **{derniere_maj}**")
    
    # --- LISTE DES ATTRACTIONS ---
    liste_attractions = sorted(df['ride_name'].unique())
    
    for ride in liste_attractions:
        ride_df = df[df['ride_name'] == ride].sort_values('created_at')
        
        if not ride_df.empty:
            st.header(f"📍 {ride}")
            
            # État actuel
            last_row = ride_df.iloc[-1]
            statut = "🟢 OUVERT" if last_row['is_open'] else "🔴 FERMÉ / EN PANNE"
            
            # Metrics
            c1, c2, c3 = st.columns(3)
            c1.metric("Statut", statut)
            c2.metric("Attente", f"{last_row['wait_time']} min")
            
            # Calcul des pannes (changement True -> False)
            ride_df['switched_off'] = (ride_df['is_open'] == False) & (ride_df['is_open'].shift(1) == True)
            nb_pannes = ride_df['switched_off'].sum()
            c3.metric("Pannes (Aujourd'hui)", nb_pannes)

            # --- GRAPHIQUE D'ÉVOLUTION STATIQUE ---
            st.subheader("📈 Évolution de l'attente")
            
            if not ride_df.empty:
                # 1. Préparation des données (arrondi à 5min)
                chart_data = ride_df.copy()
                chart_data['created_at'] = chart_data['created_at'].dt.round('5min')
                
                # 2. Création du graphique Altair SANS interaction
                chart = alt.Chart(chart_data).mark_area(
                    line={'color':'#29b5e8'},
                    color=alt.Gradient(
                        gradient='linear',
                        stops=[alt.GradientStop(color='#29b5e8', offset=0),
                               alt.GradientStop(color='rgba(41, 181, 232, 0.1)', offset=1)],
                        x1=1, x2=1, y1=1, y2=0
                    )
                ).encode(
                    x=alt.X('created_at:T', title=None, axis=alt.Axis(grid=False)),
                    y=alt.Y('wait_time:Q', title="Minutes", axis=alt.Axis(grid=True)),
                    tooltip=[] # On vide les tooltips pour qu'il ne se passe rien au survol
                ).properties(
                    height=250
                ).configure_view(
                    strokeWidth=0 # Enlève la bordure
                ).interactive(False) # <--- LA LIGNE MAGIQUE : Désactive tout mouvement
            
                st.altair_chart(chart, use_container_width=True)
            
            # --- DÉTAIL DES PANNES ---
            if nb_pannes > 0:
                with st.expander("🔎 Historique des coupures"):
                    pannes_detectees = ride_df[ride_df['switched_off'] == True]
                    for _, p in pannes_detectees.iterrows():
                        st.warning(f"⚠️ Panne détectée vers {p['created_at'].strftime('%H:%M')}")
        
        st.divider()
else:
    st.warning("⚠️ Aucune donnée pour aujourd'hui. Lancez le 'Disney Check' sur GitHub pour démarrer le suivi !")

# --- BOUTON DE RAFRAÎCHISSEMENT MANUEL ---
if st.button('🔄 Actualiser la page'):
    st.rerun()
