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

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

def send_discord_alert(ride_name, is_open, wait_time):
    if not DISCORD_WEBHOOK_URL:
        return

    # Style du message
    color = 0x2ECC71 if is_open else 0xE74C3C # Vert pour réouverture, Rouge pour panne
    status_text = "✅ RÉOUVERTURE" if is_open else "⚠️ INTERRUPTION"
    emoji = "🎢"
    
    payload = {
        "embeds": [{
            "title": f"{emoji} {status_text}",
            "description": f"**{ride_name}** est désormais {'ouvert' if is_open else 'en panne'}.",
            "color": color,
            "fields": [
                {"name": "Temps d'attente", "value": f"{wait_time} min", "inline": True},
                {"name": "Heure", "value": datetime.now().strftime("%H:%M"), "inline": True}
            ],
            "footer": {"text": "Disney Tracker Live Update"}
        }]
    }
    
    try:
        requests.post(DISCORD_WEBHOOK_URL, json=payload)
    except Exception as e:
        print(f"Erreur Webhook: {e}")

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
    PARIS_ID = "e8d0207f-da8a-4048-bec8-117aa946b2c2"
    url = f"https://api.themeparks.wiki/v1/entity/{PARIS_ID}/live"
    
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json().get('liveData', [])
        
        # On récupère l'heure actuelle AVEC information de timezone (UTC)
        now = datetime.now(timezone.utc)
        count = 0

        for item in data:
            if item.get('entityType') == 'SHOW':
                show_name = item.get('name')
                slots = item.get('showtimes', [])
                
                if not slots:
                    continue

                for slot in slots:
                    start_str = slot.get('startTime')
                    if not start_str: continue
                    
                    # L'API renvoie "2026-05-04T22:30:00+02:00"
                    # fromisoformat() comprend le "+02:00" et crée un objet offset-aware
                    start_dt = datetime.fromisoformat(start_str)
                    
                    # La comparaison est maintenant safe : UTC vs UTC+2 géré par Python
                    is_performed = now > start_dt

                    park_id = item.get('parkId', '')
                    park_name = "DAW" if park_id == "ca888437-ebb4-4d50-aed2-d227f7096968" else "DLP"

                    supabase.table("show_times").upsert({
                        "show_name": show_name,
                        "park": park_name,
                        "location": item.get('location', 'Disneyland Paris'),
                        "start_time": start_str, # On garde le string original avec l'offset (+02:00)
                        "is_performed": is_performed,
                        "updated_at": now.isoformat()
                    }, on_conflict="show_name, start_time").execute()
                    
                    count += 1
        
        print(f"🎭 Shows : {count} performances synchronisées (TimeZone Corrected).")

    except Exception as e:
        print(f"❌ Erreur Shows: {e}")

def fetch_park_schedules():
    PARK_IDS = {
        "DLP": "dae968d5-630d-4719-8b06-3d107e944401",
        "DAW": "ca888437-ebb4-4d50-aed2-d227f7096968"
    }
    
    for code, pid in PARK_IDS.items():
        url = f"https://api.themeparks.wiki/v1/entity/{pid}/schedule"
        try:
            response = requests.get(url, timeout=15)
            schedule_data = response.json()
            
            # On traite les entrées de planning (souvent les 30 prochains jours)
            for entry in schedule_data:
                day_date = entry.get('date')
                st = entry.get('openingTime')
                et = entry.get('closingTime')
                type_session = entry.get('type')

                # Préparation des données pour l'upsert
                payload = {
                    "park_id": code,
                    "date": day_date,
                    "updated_at": datetime.now().isoformat()
                }

                if type_session == "OPERATING":
                    payload["opening_time"] = st
                    payload["closing_time"] = et
                elif type_session == "EXTRA_MAGIC_HOURS":
                    payload["emt_opening_time"] = st
                    payload["emt_closing_time"] = et

                supabase.table("park_schedule").upsert(payload, on_conflict="park_id, date").execute()
            
            print(f"📅 Horaires synchronisés pour {code}")
        except Exception as e:
            print(f"❌ Erreur horaires {code}: {e}")

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
        # ON AJOUTE L'HISTORIQUE ICI
            supabase.table("ride_history").insert({
                "ride_name": official_name,
                "wait_time": wait,
                "last_updated": datetime.now().isoformat()
            }).execute()
        
            handle_breakdown_logic(official_name, status)
            return True
        
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
    fetch_and_sync()
    fetch_shows()
    fetch_park_schedules()