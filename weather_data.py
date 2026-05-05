import requests
import os
from datetime import datetime
import pytz
from supabase import create_client

# Configuration via les variables d'environnement de GitHub
URL = os.environ.get("SUPABASE_URL")
KEY = os.environ.get("SUPABASE_KEY")
supabase = create_client(URL, KEY)

def sync_weather():
    lat, lon = 48.8675, 2.7841
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,apparent_temperature,weather_code,wind_speed_10m,wind_gusts_10m&timezone=Europe%2FParis"
    
    try:
        response = requests.get(url)
        data = response.json()['current']
        
        entry = {
            "id": 1,
            "created_at": datetime.now(pytz.timezone('Europe/Paris')).isoformat(),
            "temp": data['temperature_2m'],
            "feels_like": data['apparent_temperature'],
            "wind_speed": data['wind_speed_10m'],
            "wind_gusts": data['wind_gusts_10m'], # Nouvelle donnée !
            "weather_code": data['weather_code']
        }
        
        supabase.table("weather_logs").upsert(entry, on_conflict="id").execute()
        print(f"✅ Sync OK : {data['temperature_2m']}°C | Rafales : {data['wind_gusts_10m']} km/h")
        
    except Exception as e:
        print(f"❌ Erreur : {e}")

if __name__ == "__main__":
    sync_weather()