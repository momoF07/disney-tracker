import streamlit as st
from modules.emojis import get_emoji

def render_weather_card(weather):
    if not weather: return

    from modules.weather import info_weather_code, info_msc, info_dsp
    ressenti = weather.get('feels_like')
    
    alert_77 = info_weather_code(ressenti)
    msc = info_msc(ressenti)
    dsp = info_dsp(ressenti)

    # Construction sécurisée du HTML
    alert_html = ""
    if alert_77:
        alert_html = f"""<div style="margin-top: 15px; padding: 12px; background: {alert_77['color']}; border-radius: 12px; text-align: center; color: white; font-size: 13px; font-weight: 600;">⚠️ {alert_77['code']} : {alert_77['sub']}</div>"""

    shows_html = ""
    if msc or dsp:
        def get_box(title, data):
            if not data: return ""
            return f"""<div style="flex: 1; min-width: 180px; padding: 12px; background: {data['bg']}; border-radius: 15px; border: 1px solid {data['color']}; color: {data['color']}; font-size: 11px; line-height: 1.4;"><b style="font-size: 13px; display: block; margin-bottom: 4px; text-transform: uppercase;">{title} • {data['t']}</b><span style="opacity: 0.9;">{data['msg']}</span></div>"""
        
        shows_html = f"""<div style="display: flex; gap: 10px; margin-top: 15px; flex-wrap: wrap;">{get_box("🎨 MSC", msc)}{get_box("🎭 DSP", dsp)}</div>"""

    # Bloc principal : On enlève les indentations pour éviter que Streamlit ne croit à un bloc de code
    html_final = f"""<div style="background: rgba(255,255,255,0.05); padding: 20px; border-radius: 24px; border: 1px solid rgba(255,255,255,0.1); margin-bottom: 25px; backdrop-filter: blur(10px);"><div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 15px;"><div style="display: flex; align-items: center; gap: 20px;"><span style="font-size: 50px; filter: drop-shadow(0 0 10px rgba(255,255,255,0.2));">{weather['emoji']}</span><div><b style="color: white; font-size: 20px; display: block;">{weather['desc']}</b><span style="color: rgba(148, 163, 184, 0.8); font-size: 12px; font-weight: 500;">📍 Marne-la-Vallée, France</span></div></div><div style="text-align: right; min-width: 150px;"><div style="margin-bottom: 8px;"><span style="color: white; font-size: 24px; font-weight: 800;">{weather['temp']}°C</span><span style="color: rgba(255,255,255,0.5); font-size: 14px; margin-left: 5px;">(Ressenti {ressenti}°)</span></div><div style="color: rgba(255,255,255,0.7); font-size: 12px; font-weight: 600; letter-spacing: 0.5px;">💨 {weather['wind']} <span style="opacity:0.4; margin: 0 5px;">|</span> 🚩 {weather['gusts']}</div></div></div>{alert_html}{shows_html}</div>"""

    st.markdown(html_final, unsafe_allow_html=True)

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

def render_park_hours(schedules):
    """Affiche les horaires d'ouverture des deux parcs"""
    # Filtrer les horaires de type PARK
    parks = [s for s in schedules if s.get('type') == 'PARK']
    
    html_boxes = ""
    for p in parks:
        name = "Disneyland Park" if "Disneyland" in p['ride_name'] else "Adventure World"
        color = "#4facfe" if "Disneyland" in p['ride_name'] else "#fb923c"
        
        html_boxes += f"""
        <div style="flex: 1; min-width: 140px; padding: 15px; background: rgba(255,255,255,0.03); 
                    border-radius: 18px; border-left: 4px solid {color};">
            <div style="font-size: 10px; color: #94a3b8; font-weight: 800; letter-spacing: 1px;">{name.upper()}</div>
            <div style="font-size: 18px; color: white; font-weight: 700; margin-top: 5px;">{p['opening_time']} — {p['closing_time']}</div>
        </div>"""

    st.markdown(f"""
    <div style="background: rgba(255,255,255,0.05); padding: 20px; border-radius: 24px; border: 1px solid rgba(255,255,255,0.1); margin-bottom: 20px; backdrop-filter: blur(10px);">
        <div style="color: white; font-size: 14px; font-weight: 700; margin-bottom: 15px; display: flex; align-items: center; gap: 10px;">
            🕒 HORAIRES DES PARCS
        </div>
        <div style="display: flex; gap: 12px; flex-wrap: wrap;">{html_boxes}</div>
    </div>
    """, unsafe_allow_html=True)

def render_upcoming_shows(schedules):
    """Affiche les spectacles dans les 2 prochaines heures"""
    now = datetime.now().strftime("%H:%M")
    # Simulation de filtrage 2h (simplifié pour l'exemple)
    shows = [s for s in schedules if s.get('type') == 'SHOW' and s['opening_time'] >= now]
    shows = sorted(shows, key=lambda x: x['opening_time'])[:3] # Top 3 prochains

    show_items = ""
    if not shows:
        show_items = '<div style="color: #64748b; font-size: 12px; padding: 10px;">Pas de shows prévus prochainement.</div>'
    else:
        for s in shows:
            show_items += f"""
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px; background: rgba(255,255,255,0.02); border-radius: 12px; margin-bottom: 8px;">
                <span style="color: white; font-size: 13px; font-weight: 600;">✨ {s['ride_name']}</span>
                <span style="color: #a78bfa; font-size: 13px; font-weight: 800; background: rgba(167, 139, 250, 0.1); padding: 2px 8px; border-radius: 6px;">{s['opening_time']}</span>
            </div>"""

    st.markdown(f"""
    <div style="background: rgba(255,255,255,0.05); padding: 20px; border-radius: 24px; border: 1px solid rgba(255,255,255,0.1); margin-bottom: 20px; backdrop-filter: blur(10px);">
        <div style="color: white; font-size: 14px; font-weight: 700; margin-bottom: 15px;">🎭 PROCHAINS SPECTACLES</div>
        {show_items}
    </div>
    """, unsafe_allow_html=True)