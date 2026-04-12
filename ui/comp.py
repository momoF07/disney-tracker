import streamlit as st
from modules.emojis import get_emoji

def render_weather_card(w):
    if not w:
        st.warning("⚠️ Météo indisponible")
        return

    # On récupère l'alerte à l'intérieur de la fonction
    from modules.weather import info_weather
    alert = info_weather(w['feels_like'])

    # Conteneur principal pour la météo
    with st.container(border=True):
        col1, col2, col3 = st.columns([1, 1, 1.5])
        
        col1.metric("Température", f"{w['temp']}°C")
        col2.metric("Ressenti", f"{w['feels_like']}°C")
        
        with col3:
            st.markdown(f"**{w['emoji']} {w['desc']}**")
            st.caption(f"💨 Vent : {w['wind']}")

        # SI une alerte existe, on l'ajoute EN BAS de la même boîte
        if alert:
            st.markdown(f"""
                <div style="
                    background-color: {alert['color']};
                    color: white;
                    padding: 8px;
                    border-radius: 8px;
                    text-align: center;
                    margin-top: 10px;
                    font-size: 14px;
                ">
                    <b>⚠️ CODE {alert['msg']}</b> : {alert['sub']}
                </div>
            """, unsafe_allow_html=True)

def render_api_info(api_time, refresh_time):
    """Affiche le bandeau d'état de l'API et du dernier refresh"""
    st.markdown(f"""
    <div style="background:rgba(255,255,255,0.05); padding:12px; border-radius:15px; border-left:4px solid #4facfe; margin-bottom:15px;">
        <div style="display:flex; justify-content:space-between; width:100%;">
            <div><span style="color:#94a3b8; font-size:12px;">API:</span> <b style="color:white;">{api_time}</b></div>
            <div><span style="color:#94a3b8; font-size:12px;">Refresh:</span> <b style="color:white;">{refresh_time}</b></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_ride_card(ride, sub, wait, bg, card_style, pill, show_wait=True):
    """Affiche la carte d'attraction. Le carré de droite est rendu conditionnellement."""
    
    # 1. On initialise les variables pour éviter les erreurs UnboundLocalError
    wait_section = ""
    flex_style = ""

    # 2. On construit le bloc de droite UNIQUEMENT si show_wait est True
    if show_wait:
        wait_html = f'<span class="wait-val">{wait}</span>'
        if str(wait).isdigit():
            wait_html += '<span class="wait-unit">min</span>'

        # On stocke tout le carré HTML dans cette variable
        wait_section = f"""<div class="ride-right-wait {bg}">
                <span style="font-size:10px; opacity:0.7;">ATTENTE</span>
                {wait_html}
            </div>"""
        
    else:
        # Si on cache le carré, on demande à la partie gauche de s'étendre
        flex_style = "flex-grow: 1;"

    # Si show_wait=False, cette variable est vide (""), donc rien ne s'affiche et rien ne plante
    st.markdown(f"""
    <div class="ride-row">
        <div class="ride-left-card {card_style}" style="{flex_style}">
            <div class="ride-info-meta">
                <span style="font-size:24px;">{get_emoji(ride)}</span>
                <div class="ride-titles">
                    <p class="ride-main-name">{ride}</p>
                    <p class="ride-sub-status">{sub}</p>
                </div>
            </div>
            <div class="state-pill">{pill}</div>
        </div>
        {wait_section}
    </div>
    """, unsafe_allow_html=True)