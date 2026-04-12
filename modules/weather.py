import requests

def get_disney_weather():
    # Coordonnées de Chessy (Marne-la-Vallée)
    lat, lon = 48.8675, 2.7841
    
    # Ajout de 'apparent_temperature' dans la liste des paramètres 'current'
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,apparent_temperature,weather_code,wind_speed_10m&timezone=Europe%2FParis"
    
    try:
        response = requests.get(url, timeout=5)
        data = response.json().get('current', {})
        
        temp = data.get('temperature_2m')
        apparent_temp = data.get('apparent_temperature') # Récupération du ressenti
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
        
        return {
            "temp": f"Température : {temp}",
            "feels_like": f"{apparent_temp}°C",
            "wind": f"{wind} km/h",
            "desc": desc,
            "emoji": emoji
        }
    except Exception as e:
        print(f"Erreur météo : {e}")
        return None

# Test
weather = get_disney_weather()
if weather:
    print(f"Météo Disney : {weather['emoji']} {weather['desc']}")
    print(f"Température : {weather['temp']} (Ressenti : {weather['feels_like']})")
    print(f"Vent : {weather['wind']}")


def info_weather(feels_like):
    """Génère les infos d'alerte basées sur le ressenti."""
    if feels_like >= 30:
        return {
            "code": "77+",
            "color": "#FF4B4B", # Rouge
            "msg": "🌡️ ALERTE CHALEUR EXTRÊME : CODE 77+",
            "sub": "Hydratation prioritaire. Cherchez l'ombre et la clim."
        }
    elif feels_like >= 25:
        return {
            "code": "77",
            "color": "#FFA500", # Orange
            "msg": "⚠️ ALERTE CHALEUR : CODE 77",
            "sub": "Pensez à boire régulièrement de l'eau."
        }
    return None