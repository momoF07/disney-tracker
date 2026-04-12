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
    """Affiche la carte d'attraction. Le carré de droite est rendu conditionnellement."""
    
    wait_section_html = ""
    flex_style = "flex: 1;"  # Par défaut, la carte gauche prend tout l'espace

    if show_wait:
        wait_html = f'<span class="wait-val">{wait}</span>'
        if str(wait).isdigit():
            wait_html += '<span class="wait-unit">min</span>'
        
        wait_section_html = f"""
            <div class="ride-right-wait {bg}">
                <span style="font-size:10px; opacity:0.7;">ATTENTE</span>
                {wait_html}
            </div>
        """
        flex_style = ""  # On retire le flex:1 pour laisser de la place au carré
    
    st.markdown(f"""
    <style>
        .ride-row {{
            display: flex;
            align-items: stretch;
            gap: 8px;
            margin-bottom: 8px;
        }}
        .ride-left-card {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex: 1;
            padding: 12px 16px;
            border-radius: 12px;
        }}
        .ride-info-meta {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .ride-titles {{
            display: flex;
            flex-direction: column;
        }}
        .ride-main-name {{
            margin: 0;
            font-weight: bold;
            font-size: 15px;
        }}
        .ride-sub-status {{
            margin: 0;
            font-size: 12px;
            opacity: 0.8;
        }}
        .state-pill {{
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: bold;
            background: rgba(255,255,255,0.15);
        }}
        .ride-right-wait {{
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-width: 80px;
            width: 80px;
            border-radius: 12px;
            padding: 10px 8px;
            gap: 2px;
        }}
        .wait-val {{
            font-size: 22px;
            font-weight: bold;
            line-height: 1;
        }}
        .wait-unit {{
            font-size: 11px;
            opacity: 0.8;
        }}
    </style>
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
        {wait_section_html}
    </div>
    """, unsafe_allow_html=True)