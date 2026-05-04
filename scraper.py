import os
import requests
import config as cfg # Importe ton fichier config.py
from supabase import create_client
from datetime import datetime

# --- CONFIGURATION ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# IDs officiels ThemeparksWiki
PARKS = {
    "DLP": "dae968d5-630d-4719-8b06-3d107e944401", # Disneyland Park
    "DAW": "ca888437-ebb4-4d50-aed2-d227f7096968"  # Disney Adventure World
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
    api_name = item['name']
    
    # --- LOGIQUE DE CORRESPONDANCE DES NOMS ---
    # On reconstruit le nom exact avec l'émoji tel qu'il est dans rides_info
    # Exemple: "Big Thunder Mountain" -> "Big Thunder Mountain ⛰️"
    emoji = cfg.get_emoji(api_name)
    
    # Si l'émoji est trouvé et n'est pas déjà dans le nom, on l'ajoute
    # (Adaptation selon comment tu as rempli rides_info via init_db)
    full_name = f"{api_name} {emoji}".strip() if emoji != "🎡" else api_name
    
    # DEBUG pour voir ce qui est envoyé
    print(f"DEBUG: API dit '{api_name}' -> On cherche '{full_name}'")

    status = item['status']
    wait = item.get('queue', {}).get('STANDBY', {}).get('waitTime', 0)
    is_open = (status == 'OPERATING')

    try:
        # 1. Mise à jour de la table Live
        # L'upsert ne marchera QUE si full_name existe déjà dans rides_info
        supabase.table("disney_live").upsert({
            "ride_name": full_name, 
            "wait_time": wait,
            "is_open": is_open,
            "status": status,
            "last_updated": "now()"
        }, on_conflict="ride_name").execute()

        # 2. Logique de détection de Panne (101)
        handle_breakdown_logic(full_name, status)
        
    except Exception as e:
        print(f"⚠️ Erreur insertion pour {full_name}: {e}")

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