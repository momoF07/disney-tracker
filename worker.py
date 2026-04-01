import requests
import os
from supabase import create_client
from datetime import datetime

# Configuration Supabase
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

PARKS = ["dae968d5-630d-4719-8b06-3d107e944401", "ca888437-ebb4-4d50-aed2-d227f7096968"]

def run_worker():
    # --- LOGIQUE DE RESET (02h00 Paris) ---
    now_utc = datetime.utcnow()
    if now_utc.hour in [0, 1] and now_utc.minute < 20:
        try:
            supabase.table("disney_logs").delete().gt("id", 0).execute()
            print(f"🌙 Reset de nuit effectué.")
        except Exception as e:
            print(f"Erreur Reset : {e}")

    # --- COLLECTE DES DONNÉES ---
    for p_id in PARKS:
        try:
            response = requests.get(f"https://api.themeparks.wiki/v1/entity/{p_id}/live", timeout=15)
            data = response.json()
            
            for ride in data.get('liveData', []):
                if ride.get('entityType') == "ATTRACTION":
                    name = ride['name']
                    is_open = (ride.get('status') == "OPERATING")
                    
                    queue = ride.get('queue', {})
                    standby = queue.get('STANDBY', {}) if queue else {}
                    wait = standby.get('waitTime', 0) if standby else 0

                    # --- LOGIQUE D'ÉCONOMIE DE LIGNES ---
                    # 1. Récupérer le tout dernier état en base pour cette attraction
                    last_record = supabase.table("disney_logs")\
                        .select("wait_time, is_open")\
                        .eq("ride_name", name)\
                        .order("created_at", desc=True)\
                        .limit(1)\
                        .execute()
                    
                    should_write = True
                    if last_record.data:
                        last_wait = last_record.data[0]['wait_time']
                        last_open = last_record.data[0]['is_open']
                        
                        # 2. Si rien n'a changé, on ne réécrit pas la même chose
                        if last_wait == wait and last_open == is_open:
                            should_write = False

                    if should_write:
                        # On nettoie l'ancien record "ouvert" uniquement si on va en écrire un nouveau
                        if is_open:
                            supabase.table("disney_logs").delete().eq("ride_name", name).eq("is_open", True).execute()
                        
                        # Insertion du nouvel état
                        supabase.table("disney_logs").insert({
                            "ride_name": name,
                            "wait_time": wait,
                            "is_open": is_open,
                            "created_at": datetime.utcnow().isoformat()
                        }).execute()
                        
            print(f"✅ Synchro terminée pour {p_id}")
        except Exception as e:
            print(f"❌ Erreur : {e}")

if __name__ == "__main__":
    run_worker()
