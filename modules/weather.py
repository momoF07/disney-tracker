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

def info_weather(feels_like):
    """Calcule le code 77/77+ sans affichage."""
    try:
        val = float(feels_like)
        if val >= 30:
            return {"color": "#FF4B4B", "msg": "77+", "sub": "Chaleur extrême : Hydratez-vous !"}
        elif val >= 25:
            return {"color": "#FFA500", "msg": "77", "sub": "Chaleur : Buvez de l'eau."}
    except:
        pass
    return None