import os
import requests
from supabase import create_client
from datetime import datetime
import config as cfg # Import de ta config pour les émojis

# --- CONFIGURATION ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# IDs Destination (Paris)
PARKS = {
    "DLP": "dae968d5-630d-4719-8b06-3d107e944401", # Disneyland Park (P1)
    "DAW": "ca888437-ebb4-4d50-aed2-d227f7096968"  # Disney Adventure World (P2)
}

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def fetch_and_sync():
    for park_code, park_id in PARKS.items():
        print(f"🔄 Scraping {park_code} ({park_id})...")
        url = f"https://api.themeparks.wiki/v1/entity/{park_id}/live"
        
        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            raw_data = response.json()
            
            # L'API utilise 'liveData' au lieu de 'live' sur ces IDs
            data = raw_data.get('liveData', [])
            
            # Si jamais c'est encore vide, on tente un dernier repli sur 'live'
            if not data:
                data = raw_data.get('live', [])

            print(f"📊 {park_code} : {len(data)} entités trouvées dans liveData.")
            
            for item in data:
                # Dans liveData, entityType est souvent présent
                # On traite si c'est une attraction
                if item.get('entityType', '').upper() == 'ATTRACTION':
                    process_ride(item)
                # Parfois l'API ne met pas entityType dans liveData mais le nom suffit
                # Si tu vois que le compteur est bon mais rien ne s'insère, 
                # on pourra retirer la condition entityType.
                    
        except Exception as e:
            print(f"❌ Erreur critique sur {park_code}: {e}")
            
def process_ride(item):
    api_name = item['name']
    
    # --- LOGIQUE DE CORRESPONDANCE ---
    # On vérifie si l'émoji est déjà dans le nom, sinon on l'ajoute
    emoji = cfg.get_emoji(api_name)
    full_name = api_name if emoji in api_name else f"{api_name} {emoji}".strip()

    status = item.get('status', 'CLOSED')
    wait = item.get('queue', {}).get('STANDBY', {}).get('waitTime', 0)
    is_open = (status == 'OPERATING')

    try:
        # Upsert vers Supabase
        res = supabase.table("disney_live").upsert({
            "ride_name": full_name,
            "wait_time": wait,
            "is_open": is_open,
            "status": status,
            "last_updated": datetime.now().isoformat()
        }, on_conflict="ride_name").execute()
        
        # Log pour confirmer l'envoi
        if res.data:
            print(f"✅ Synced: {full_name} ({wait} min)")
        
        # Logique de panne
        handle_breakdown_logic(full_name, status)
        
    except Exception as e:
        # Si ça échoue ici, c'est sûrement la Foreign Key
        print(f"⚠️ Erreur Supabase pour {full_name}: {e}")

def handle_breakdown_logic(name, current_status):
    try:
        open_log = supabase.table("logs_101").select("*").eq("ride_name", name).is_("end_time", "null").execute()

        if current_status == "DOWN" and not open_log.data:
            supabase.table("logs_101").insert({"ride_name": name, "start_time": datetime.now().isoformat()}).execute()
            print(f"🚨 PANNE : {name}")

        elif current_status == "OPERATING" and open_log.data:
            log_id = open_log.data[0]['id']
            supabase.table("logs_101").update({
                "end_time": datetime.now().isoformat(),
                "duration_minutes": 10 # Simplifié pour test
            }).eq("id", log_id).execute()
            print(f"✅ RÉOUVERTURE : {name}")
    except:
        pass # On ne bloque pas le scraper pour les logs

if __name__ == "__main__":
    fetch_and_sync()