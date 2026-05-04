import os
import requests
from supabase import create_client
from datetime import datetime

# --- CONFIGURATION ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# IDs officiels ThemeparksWiki
PARKS = {
    "DLP": "e8d0207f-da8a-4048-bec8-117aa946b2c2", # Disneyland Park
    "DAW": "1c7f55f2-9591-4d3a-b850-89196b05786f"  # Disney Adventure World
}

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def fetch_and_sync():
    for park_code, park_id in PARKS.items():
        print(f"🔄 Scraping {park_code}...")
        url = f"https://api.themeparks.wiki/v1/entity/{park_id}/live"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json().get('live', [])
            
            for item in data:
                if item.get('entityType') == 'ATTRACTION':
                    process_ride(item)
                    
        except Exception as e:
            print(f"❌ Erreur sur {park_code}: {e}")

def process_ride(item):
    name = item['name']
    status = item['status'] # OPERATING, DOWN, CLOSED, REFURBISHMENT
    wait = item.get('queue', {}).get('STANDBY', {}).get('waitTime', 0)
    is_open = (status == 'OPERATING')

    # 1. Mise à jour de la table Live (Upsert)
    supabase.table("disney_live").upsert({
        "ride_name": name,
        "wait_time": wait,
        "is_open": is_open,
        "status": status,
        "last_updated": "now()"
    }, on_conflict="ride_name").execute()

    # 2. Logique de détection de Panne (101)
    handle_breakdown_logic(name, status)

def handle_breakdown_logic(name, current_status):
    # On vérifie si un log est déjà ouvert pour cette attraction
    open_log = supabase.table("logs_101")\
        .select("*")\
        .eq("ride_name", name)\
        .is_("end_time", "null")\
        .execute()

    # SI status = DOWN et aucun log ouvert -> On crée un log
    if current_status == "DOWN" and not open_log.data:
        supabase.table("logs_101").insert({
            "ride_name": name,
            "start_time": datetime.now().isoformat(),
            "reason": "Technical"
        }).execute()
        print(f"🚨 PANNE DÉTECTÉE : {name}")

    # SI status = OPERATING et un log est ouvert -> On ferme le log
    elif current_status == "OPERATING" and open_log.data:
        log_id = open_log.data[0]['id']
        start_time = datetime.fromisoformat(open_log.data[0]['start_time'].replace('Z', '+00:00'))
        end_time = datetime.now()
        
        # Calcul de la durée
        duration = int((end_time.timestamp() - start_time.timestamp()) / 60)

        supabase.table("logs_101").update({
            "end_time": end_time.isoformat(),
            "duration_minutes": duration
        }).eq("id", log_id).execute()
        print(f"✅ RÉOUVERTURE : {name} (Panne de {duration} min)")

if __name__ == "__main__":
    fetch_and_sync()