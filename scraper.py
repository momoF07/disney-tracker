import requests
from datetime import datetime, timezone, timedelta
from supabase import create_client
import os

# Config (à adapter avec tes env vars)
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def clean_old_data():
    """Supprime les données de plus de 48h pour garder Supabase léger"""
    limit = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
    supabase.table("ride_history").delete().lt("last_updated", limit).execute()

def fetch_all():
    PARIS_ID = "e8d0207f-da8a-4048-bec8-117aa946b2c2"
    url = f"https://api.themeparks.wiki/v1/entity/{PARIS_ID}/live"
    
    res = requests.get(url).json().get('liveData', [])
    now = datetime.now(timezone.utc)

    for item in res:
        name = item.get('name')
        
        # 1. Update Live Table
        if item.get('entityType') == 'ATTRACTION':
            wait = item.get('queue', {}).get('STANDBY', {}).get('waitTime', 0)
            is_open = item.get('status') == 'OPERATING'
            
            supabase.table("disney_live").upsert({
                "ride_name": name, "wait_time": wait, "is_open": is_open, "updated_at": now.isoformat()
            }).execute()

            # 2. Insert into History (Seulement si ouvert pour ne pas fausser les moyennes)
            if is_open:
                supabase.table("ride_history").insert({
                    "ride_name": name, "wait_time": wait, "last_updated": now.isoformat()
                }).execute()

    # 3. Nettoyage
    clean_old_data()

if __name__ == "__main__":
    fetch_all()