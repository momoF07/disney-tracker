import requests
import streamlit as st

#@st.cache_data(ttl=150)
def get_disney_weather():
    lat, lon = 48.8675, 2.7841
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,apparent_temperature,weather_code,wind_speed_10m,wind_gusts_10m&timezone=Europe%2FParis"

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        res_json = response.json()
        data = res_json.get('current', {})
        
        # Sécurisation des valeurs : on remplace None par 0 ou "--"
        def clean_val(val, default=0):
            return val if val is not None else default

        temp = clean_val(data.get('temperature_2m'), "--")
        apparent_temp = clean_val(data.get('apparent_temperature'), "--")
        wind = clean_val(data.get('wind_speed_10m'), 0)
        gusts = clean_val(data.get('wind_gusts_10m'), 0)
        code = data.get('weather_code', -1)
        
        # Map étendue pour éviter le "Inconnu" sur les codes intermédiaires
        weather_map = {
            0: ("☀️", "Ciel dégagé"),
            1: ("🌤️", "Plutôt beau"), 2: ("⛅", "Partiellement nuageux"), 3: ("☁️", "Couvert"),
            45: ("🌫️", "Brouillard"), 48: ("🌫️", "Brouillard givrant"),
            51: ("🌦️", "Bruine"), 53: ("🌦️", "Bruine"), 55: ("🌦️", "Bruine"),
            61: ("🌧️", "Pluie faible"), 63: ("🌧️", "Pluie modérée"), 65: ("🌧️", "Pluie forte"),
            71: ("❄️", "Neige faible"), 73: ("❄️", "Neige"), 75: ("❄️", "Neige forte"),
            80: ("🌦️", "Averses"), 81: ("🌦️", "Averses"), 82: ("🌦️", "Averses"),
            95: ("⛈️", "Orage"), 96: ("⛈️", "Orage"), 99: ("⛈️", "Orage")
        }
        
        emoji, desc = weather_map.get(code, ("🌡️", "Météo stable"))
        
        return {
            "temp": temp,
            "feels_like": apparent_temp,
            "wind": f"{round(wind)} km/h",
            "gusts": f"{round(gusts)} km/h",
            "desc": desc,
            "emoji": emoji,
            "success": True
        }
    except Exception as e:
        # En cas d'erreur, on retourne un dictionnaire "safe" pour ne pas planter l'UI
        return {
            "temp": "10", "feels_like": "10", 
            "wind": "10 km/h", "gusts": "10 km/h", 
            "desc": "Météo indisponible, ne pas tenir compte des valeurs", "emoji": "⚠️",
            "success": False
        }
def info_weather_code(feels_like):
    if feels_like is None:
        return None
    try:
        val = float(feels_like)
        
        # 1. TEST
        if val >= 999:
            return {
                "code": "Test",
                "color": "#3B82F6", # Ton bleu aléatoire
                "msg": "🌟 ALERTE CHALEUR DE TEST : CODE TEST",
                "sub": "Pensez à désactiver."
            }
        # 2. 77+
        elif val >= 30:
            return {
                "code": "77+",
                "color": "#FF4B4B",
                "msg": "🌡️ ALERTE CHALEUR EXTRÊME : CODE 77+",
                "sub": "Hydratation prioritaire. Cherchez l'ombre."
            }
        # 3. 77
        elif val >= 25:
            return {
                "code": "77",
                "color": "#FFA500",
                "msg": "⚠️ ALERTE CHALEUR : CODE 77",
                "sub": "Pensez à boire régulièrement de l'eau."
            }
    except:
        return None
    return None

def info_msc(feels_like):
    """Protocole complet Millions Splashes of Colours (MSC)."""
    if feels_like is None: 
        return None
    
    val = float(feels_like)
    
    # --- PROTOCOLE CHALEUR ---
    if val >= 38.0:
        return {"t": "Temps 5 (Chaleur)", "msg": "Show Annulé", "color": "#721c24", "bg": "#f8d7da"}
    elif 35.0 <= val <= 37.9:
        return {"t": "Temps 4 (Chaleur)", "msg": "Pas de chorégraphie (Position Meet & Greet)", "color": "#856404", "bg": "#fff3cd"}
    elif 32.0 <= val <= 34.9:
        return {"t": "Temps 3 (Chaleur)", "msg": "Mode roulage - 1/2 pour les Performers", "color": "#856404", "bg": "#fff3cd"}
    elif 27.1 <= val <= 31.9:
        return {"t": "Temps 2 (Chaleur)", "msg": "Mode roulage. Seuls les danseurs font une halte sur Central Plaza - Pyro coupée - Retrait Characters (Judy Hopps / Timon / Stitch)", "color": "#856404", "bg": "#fff3cd"}
    elif 23.1 <= val <= 27.0:
        return {"t": "Temps 1 (Chaleur)", "msg": "Chorégraphie allégée", "color": "#c67c00", "bg": "#fff3cd"}
    
    # --- ZONE NEUTRE (Temps 0) ---
    elif 10.1 <= val <= 23.0:
        return {"t": "Temps 0", "msg": "Version Hiver ou Été à la discrétion des équipes", "color": "#444", "bg": "#f0f2f6"}

    # --- PROTOCOLE FROID ---
    elif 5.0 <= val <= 10.0:
        return {"t": "Temps 1 (Froid)", "msg": "Tenues hiver & Chorégraphie allégée - Face au sol", "color": "#155724", "bg": "#d4edda"}
    elif 0.0 <= val <= 4.9:
        return {"t": "Temps 2 (Froid)", "msg": "Chorégraphie adaptée : Asha, Mirabel, Vaiana", "color": "#004085", "bg": "#cce5ff"}
    elif -4.9 <= val <= 0.1:
        return {"t": "Temps 3 (Froid)", "msg": "Mode roulage. Seuls les danseurs font une halte sur Central Plaza", "color": "#0c5460", "bg": "#d1ecf1"}
    elif -10.0 <= val <= -5.0:
        return {"t": "Temps 4 (Froid)", "msg": "Mode roulage - 1/2 pour les Performers", "color": "#856404", "bg": "#fff3cd"}
    elif -14.9 <= val <= -10.1:
        return {"t": "Temps 5 (Froid)", "msg": "Show Annulée", "color": "#721c24", "bg": "#f8d7da"}
    
    return None

def info_dsp(feels_like):
    """Protocole complet Disney Stars on Parade (DSP)."""
    if feels_like is None: return None
    val = float(feels_like)

    # --- CHALEUR DSP ---
    if val >= 38.0:
        return {"t": "Temps 5 (Chaleur)", "msg": "Parade Annulée", "color": "#721c24", "bg": "#f8d7da"}
    elif 35.0 <= val <= 37.9:
        return {"t": "Temps 4 (Chaleur)", "msg": "Characters remplacés par Faces/Performers sans têtes sculptées. Mickey/Minnie en standard.", "color": "#856404", "bg": "#fff3cd"}
    elif 32.0 <= val <= 34.9:
        return {"t": "Temps 3 (Chaleur)", "msg": "Annulation chorégraphies sol - Retrait Roue de la Destinée - Raccourci Town Square", "color": "#856404", "bg": "#fff3cd"}
    elif 28.0 <= val <= 31.9:
        return {"t": "Temps 2 (Chaleur)", "msg": "Vitesse adaptée - Annulation chorégraphies unités - Retrait Thorns et Gabrielles", "color": "#856404", "bg": "#fff3cd"}
    elif 25.0 <= val <= 27.9:
        return {"t": "Temps 1 (Chaleur)", "msg": "Alternance chorégraphie/déambulation - Retrait gants - Brumisateurs actifs", "color": "#c67c00", "bg": "#fff3cd"}

    # --- ZONE NEUTRE (Temps 0) ---
    elif 10.1 <= val <= 24.9:
        return {"t": "Temps 0", "msg": "Version Hiver/Été au choix TL - Retrait moufles/cape Frozen", "color": "#444", "bg": "#f0f2f6"}

    # --- FROID DSP ---
    elif 5.0 <= val <= 10.0:
        return {"t": "Temps 1 (Froid)", "msg": "Costumes hiver Face Characters & Bodys antifroid", "color": "#155724", "bg": "#d4edda"}
    elif 0.0 <= val <= 4.9:
        return {"t": "Temps 2 (Froid)", "msg": "Costumes hiver Face Characters & Bodys antifroid", "color": "#004085", "bg": "#cce5ff"}
    elif -4.9 <= val <= 0.1:
        return {"t": "Temps 3 (Froid)", "msg": "Costumes hiver Face Characters & Bodys antifroid", "color": "#0c5460", "bg": "#d1ecf1"}
    elif -9.9 <= val <= -5.0:
        return {"t": "Temps 4 (Froid)", "msg": "Costumes hiver Face Characters & Bodys antifroid", "color": "#856404", "bg": "#fff3cd"}
    elif val <= -10.0:
        return {"t": "Temps 5 (Froid)", "msg": "Parade Annulée", "color": "#721c24", "bg": "#f8d7da"}

    return None