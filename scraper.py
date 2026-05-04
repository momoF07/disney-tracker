import os
import requests
import re
import config as cfg
from supabase import create_client
from datetime import datetime, timezone

# --- CONFIGURATION ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

PARKS = {
    "DLP": "dae968d5-630d-4719-8b06-3d107e944401",
    "DAW": "ca888437-ebb4-4d50-aed2-d227f7096968"
}

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def super_clean(text):
    """Garde uniquement les lettres et chiffres (ignore émojis, accents, symboles)"""
    if not text: return ""
    # On met en minuscule et on ne garde que a-z et 0-9
    return re.sub(r'[^a-z0-9]', '', text.lower())

def fetch_and_sync():
    # On prépare un dictionnaire de correspondance : { 'nomnettoye': 'Nom Réel 🎡' }
    clean_allowed_map = {super_clean(name): name for name in cfg.ALL_RIDES_LIST}
    
    for park_code, park_id in PARKS.items():
        print(f"🔄 Scraping {park_code}...")
        url = f"https://api.themeparks.wiki/v1/entity/{park_id}/live"
        
        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            raw_data = response.json()
            
            data = raw_data.get('liveData', []) or raw_data.get('live', [])
            print(f"📊 {park_code} : {len(data)} entités trouvées.")
            
            for item in data:
                if item.get('entityType', '').upper() == 'ATTRACTION':
                    api_name = item.get('name', '')
                    api_name_clean = super_clean(api_name)

                    # On compare le nom de l'API nettoyé avec notre map
                    if api_name_clean in clean_allowed_map:
                        official_name = clean_allowed_map[api_name_clean]
                        process_ride(item, official_name)
                    else:
                        # Log pour voir ce qui ne matche toujours pas (ex: noms anglais vs français)
                        print(f"❌ AUCUN MATCH pour : {api_name}")
                        
        except Exception as e:
            print(f"❌ Erreur critique sur {park_code}: {e}")

def fetch_shows():
    # ID spécifique pour les shows de Paris (Destination)
    PARIS_ID = "e8d0207f-da8a-4048-bec8-117aa946b2c2"
    url = f"https://api.themeparks.wiki/v1/entity/{PARIS_ID}/live"
    
    try:
        response = requests.get(url, timeout=15)
        data = response.json().get('liveData', [])
        
        now = datetime.now(timezone.utc)
        count = 0

        for item in data:
            # On ne prend que les SHOW (et on ignore les ATTRACTION ici)
            if item.get('entityType') == 'SHOW':
                show_name = item.get('name')
                # On tente de récupérer le parc via la localisation ou un tag
                location = item.get('location', 'Disneyland Paris')
                
                # Parcours des horaires de performances
                show_times = item.get('showTimes', [])
                for slot in show_times:
                    start_str = slot.get('startTime') # Format ISO: 2024-05-20T14:30:00+00:00
                    if not start_str: continue
                    
                    start_dt = datetime.fromisoformat(start_str)
                    
                    # Logique is_performed
                    is_performed = now > start_dt

                    # Upsert dans show_times
                    supabase.table("show_times").upsert({
                        "show_name": show_name,
                        "park": "DLP" if "Disneyland Park" in location else "DAW",
                        "location": location,
                        "start_time": start_str,
                        "is_performed": is_performed,
                        "updated_at": now.isoformat()
                    }, on_conflict="show_name, start_time").execute()
                    
                    count += 1
        
        print(f"🎭 Shows : {count} performances synchronisées.")

    except Exception as e:
        print(f"❌ Erreur Scraper Shows: {e}")

def process_ride(item, official_name):
    status = item.get('status', 'CLOSED')
    wait = item.get('queue', {}).get('STANDBY', {}).get('waitTime', 0)
    is_open = (status == 'OPERATING')

    try:
        # Upsert vers Supabase
        res = supabase.table("disney_live").upsert({
            "ride_name": official_name,
            "wait_time": wait,
            "is_open": is_open,
            "status": status,
            "last_updated": datetime.now().isoformat()
        }).execute()
        
        if res.data:
            print(f"✅ Synced: {official_name} ({wait} min)")
            handle_breakdown_logic(official_name, status)
        
    except Exception as e:
        print(f"⚠️ Erreur Supabase pour {official_name}: {e}")

def handle_breakdown_logic(name, current_status):
    try:
        open_log = supabase.table("logs_101").select("*").eq("ride_name", name).is_("end_time", "null").execute()

        if current_status == "DOWN" and not open_log.data:
            supabase.table("logs_101").insert({
                "ride_name": name, 
                "start_time": datetime.now().isoformat(),
                "reason": "Technical"
            }).execute()
            print(f"🚨 PANNE DÉTECTÉE : {name}")

        elif current_status == "OPERATING" and open_log.data:
            log_id = open_log.data[0]['id']
            supabase.table("logs_101").update({
                "end_time": datetime.now().isoformat(),
                "duration_minutes": 0 
            }).eq("id", log_id).execute()
            print(f"✅ RÉOUVERTURE : {name}")
    except:
        pass

if __name__ == "__main__":
    fetch_and_sync() # Tes attractions
    fetch_shows()    # Tes spectacles