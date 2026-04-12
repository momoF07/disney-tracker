import requests

def get_disney_weather():
    lat, lon = 48.8675, 2.7841
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,apparent_temperature,weather_code,wind_speed_10m&timezone=Europe%2FParis"
    
    try:
        response = requests.get(url, timeout=5)
        data = response.json().get('current', {})
        
        # ON GARDE LES VALEURS BRUTES (NOMBRES)
        temp = data.get('temperature_2m')
        apparent_temp = data.get('apparent_temperature')
        wind = data.get('wind_speed_10m')
        code = data.get('weather_code')
        
        weather_map = {
            0: ("☀️", "Ciel dégagé"),
            1: ("🌤️", "Plutôt beau"),
            2: ("⛅", "Partiellement nuageux"),
            3: ("☁️", "Couvert"),
            45: ("🌫️", "Brouillard"),
            61: ("🌧️", "Pluie faible"),
            63: ("🌧️", "Pluie modérée"),
            71: ("❄️", "Neige"),
            80: ("🌦️", "Averses"),
            95: ("⛈️", "Orage")
        }
        
        emoji, desc = weather_map.get(code, ("❓", "Inconnu"))
        
        # RETOURNE DES NOMBRES PURS POUR LES CALCULS
        return {
            "temp": temp,           # Juste le nombre (ex: 22.5)
            "feels_like": apparent_temp, # Juste le nombre (ex: 26.0)
            "wind": f"{wind} km/h",
            "desc": desc,
            "emoji": emoji
        }
    except Exception as e:
        return None

def info_weather_code(feels_like):
    if feels_like is None:
        return None
    try:
        val = float(feels_like)
        
        # 1. TEST
        if val >= 10:
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
    """Protocole complet Show MSC (Chaleur, Neutre et Froid)."""
    if feels_like is None: 
        return None
    
    val = float(feels_like)
    
    # --- PROTOCOLE CHALEUR ---
    if val >= 38.0:
        return {"t": "Temps 5 (Chaleur)", "msg": "Code '101' (Annulé)", "color": "#721c24", "bg": "#f8d7da"}
    elif 35.0 <= val <= 37.9:
        return {"t": "Temps 4 (Chaleur)", "msg": "Pas de chorégraphie (Position Meet & Greet)", "color": "#856404", "bg": "#fff3cd"}
    elif 32.0 <= val <= 34.9:
        return {"t": "Temps 3 (Chaleur)", "msg": "Mode roulage (Code 106)", "color": "#856404", "bg": "#fff3cd"}
    elif 27.1 <= val <= 31.9:
        return {"t": "Temps 2 (Chaleur)", "msg": "Pas de Show Stop - Pyro coupée - Retrait Characters", "color": "#856404", "bg": "#fff3cd"}
    elif 23.1 <= val <= 27.0:
        return {"t": "Temps 1 (Chaleur)", "msg": "Boissons isotoniques - Chorégraphie allégée", "color": "#c67c00", "bg": "#fff3cd"}
    
    # --- ZONE NEUTRE (Temps 0) ---
    elif 10.1 <= val <= 23.0:
        return {"t": "Temps 0", "msg": "Version Hiver ou Été à la discrétion du Régisseur Scène", "color": "#444", "bg": "#f0f2f6"}

    # --- PROTOCOLE FROID ---
    elif 5.0 <= val <= 10.0:
        return {"t": "Temps 1 (Froid)", "msg": "Tenues hiver & Chorégraphie allégée", "color": "#155724", "bg": "#d4edda"}
    elif 0.0 <= val <= 4.9:
        return {"t": "Temps 2 (Froid)", "msg": "Chorégraphie adaptée : Asha, Mirabel, Vaiana", "color": "#004085", "bg": "#cce5ff"}
    elif -4.9 <= val <= 0.1:
        return {"t": "Temps 3 (Froid)", "msg": "Mode roulage. Seuls les danseurs font une halte sur Central Plaza", "color": "#0c5460", "bg": "#d1ecf1"}
    elif -10.0 <= val <= -5.0:
        return {"t": "Temps 4 (Froid)", "msg": "Les Performers effectuent un roulage sur deux", "color": "#856404", "bg": "#fff3cd"}
    elif -14.9 <= val <= -10.1:
        return {"t": "Temps 5 (Froid)", "msg": "Code '101' (Annulé)", "color": "#721c24", "bg": "#f8d7da"}
    
    return None