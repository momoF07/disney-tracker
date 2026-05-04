import os
import requests
from supabase import create_client
from datetime import datetime
import config as cfg # Import de ta config pour les émojis

# --- CONFIGURATION ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# IDs officiels (P1 et P2)
PARKS = {
    "DLP": "dae968d5-630d-4719-8b06-3d107e944401", # Disneyland Park
    "DAW": "ca888437-ebb4-4d50-aed2-d227f7096968"  # Disney Adventure World
}

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def clean_text(text):
    """Nettoie le texte pour une comparaison infaillible (sans espace, minuscule)"""
    if not text: return ""
    return "".join(text.lower().split())

def fetch_and_sync():
    # Préparation de la liste de comparaison nettoyée
    clean_allowed_list = [clean_text(name) for name in cfg.ALL_RIDES_LIST]
    
    for park_code, park_id in PARKS.items():
        print(f"🔄 Scraping {park_code} ({park_id})...")
        url = f"https://api.themeparks.wiki/v1/entity/{park_id}/live"
        
        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            raw_data = response.json()
            
            # Ciblage de la clé liveData
            data = raw_data.get('liveData', [])
            if not data:
                data = raw_data.get('live', [])

            print(f"📊 {park_code} : {len(data)} entités trouvées.")
            
            for item in data:
                # On ne traite que les attractions
                if item.get('entityType', '').upper() == 'ATTRACTION':
                    process_ride(item, clean_allowed_list)
                    
        except Exception as e:
            print(f"❌ Erreur critique sur {park_code}: {e}")

def process_ride(item, clean_allowed_list):
    api_name = item['name']
    emoji = cfg.get_emoji(api_name)
    full_name = f"{api_name} {emoji}".strip()

    # Comparaison "propre"
    current_clean_name = clean_text(full_name)

    if current_clean_name in clean_allowed_list:
        # On récupère le nom EXACT tel qu'écrit dans ton config.py
        idx = clean_allowed_list.index(current_clean_name)
        final_name_for_db = cfg.ALL_RIDES_LIST[idx]
        
        status = item.get('status', 'CLOSED')
        wait = item.get('queue', {}).get('STANDBY', {}).get('waitTime', 0)
        is_open = (status == 'OPERATING')

        try:
            # Upsert vers Supabase
            res = supabase.table("disney_live").upsert({
                "ride_name": final_name_for_db,
                "wait_time": wait,
                "is_open": is_open,
                "status": status,
                "last_updated": datetime.now().isoformat()
            }, on_conflict="ride_name").execute()
            
            if res.data:
                print(f"✅ Synced: {final_name_for_db} ({wait} min)")
            
            handle_breakdown_logic(final_name_for_db, status)
            
        except Exception as e:
            print(f"⚠️ Erreur Supabase pour {final_name_for_db}: {e}")
    else:
        # Optionnel : décommenter pour voir ce qui est rejeté
        # print(f"ℹ️ Ignoré (non listé) : {full_name}")
        pass

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
            # On ferme le log simplement
            supabase.table("logs_101").update({
                "end_time": datetime.now().isoformat(),
                "duration_minutes": 0 # Sera calculé par ta vue SQL ou Streamlit
            }).eq("id", log_id).execute()
            print(f"✅ RÉOUVERTURE : {name}")
    except:
        pass

if __name__ == "__main__":
    fetch_and_sync()