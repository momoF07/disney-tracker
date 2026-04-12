import streamlit as st
from modules.emojis import get_emoji

def render_weather_card(weather):
    """Affiche la carte météo avec alerte intégrée."""
    if not weather:
        return

    # Import local pour éviter les erreurs d'importation circulaire
    from modules.weather import info_weather
    alert = info_weather(weather.get('feels_like'))
    
    # Préparation du bloc Alerte
    alert_html = ""
    if alert:
        alert_html = f"""
        <div style="margin-top: 12px; padding: 8px; background: {alert['color']}; border-radius: 8px; text-align: center; color: white; font-size: 13px; border: 1px solid rgba(255,255,255,0.2);">
            <b>⚠️ CODE {alert['code']}</b> : {alert['msg']}
        </div>
        """

    st.markdown(f"""
    <div style="background: rgba(255,255,255,0.05); padding: 15px; border-radius: 15px; border: 1px solid rgba(255,255,255,0.1); margin-bottom: 20px;">
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <div style="display: flex; align-items: center; gap: 15px;">
                <span style="font-size: 30px;">{weather['emoji']}</span>
                <div>
                    <b style="color: white; font-size: 16px;">{weather['desc']}</b><br>
                    <span style="color: #94a3b8; font-size: 12px;">Marne-la-Vallée - Parc Disneyland</span>
                </div>
            </div>
            <div style="text-align: right;">
                <b style="color: white; font-size: 18px;">{weather['temp']}°C</b><br>
                <span style="color: white; font-size: 13px; opacity: 0.8;">Ressenti : {weather['feels_like']}°C</span><br>
                <span style="color: #94a3b8; font-size: 12px;">💨 {weather['wind']}</span>
            </div>
        </div>
        {alert_html}
    </div>
    """, unsafe_allow_html=True)