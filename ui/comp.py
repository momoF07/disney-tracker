import streamlit as st
from modules.emojis import get_emoji

def render_weather_card(weather):
    if weather:
        st.markdown(f"""
        <div style="background: rgba(255,255,255,0.05); padding: 15px; border-radius: 15px; display: flex; align-items: center; justify-content: space-between; border: 1px solid rgba(255,255,255,0.1); margin-bottom: 20px;">
            <div style="display: flex; align-items: center; gap: 15px;">
                <span style="font-size: 30px;">{weather['emoji']}</span>
                <div>
                    <b style="color: white; font-size: 16px;">{weather['desc']}</b><br>
                    <span style="color: #94a3b8; font-size: 12px;">Marne-la-Vallée</span>
                </div>
            </div>
            <div style="text-align: right;">
                <b style="color: white; font-size: 18px;">{weather['temp']}°C</b><br>
                <span style="color: #94a3b8; font-size: 12px;">💨 {weather['wind']}</span>
            </div>
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
    """Affiche la carte. Si show_wait=False, le carré de droite disparaît."""
    
    wait_section = ""
    # Si show_wait est True, on génère le carré de droite
    if show_wait:
        wait_html = f'<span class="wait-val">{wait}</span>'
        if str(wait).isdigit():
            wait_html += '<span class="wait-unit">min</span>'
        
        wait_section = f"""
            <div class="ride-right-wait {bg}">
                <span style="font-size:10px; opacity:0.7;">ATTENTE</span>
                {wait_html}
            </div>
        """

    # flex-grow: 1 assure que la carte prend toute la place si le carré est absent
    st.markdown(f"""
    <div class="ride-row">
        <div class="ride-left-card {card_style}" style="flex-grow: 1;">
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