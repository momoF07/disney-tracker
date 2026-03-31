import requests
import os
from supabase import create_client
from datetime import datetime

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

PARKS = ["dae968d5-630d-4719-8b06-3d107e944401", "ca888437-ebb4-4d50-aed2-d227f7096968"]

def run_worker():
    for p_id in PARKS:
        try:
            response = requests.get(f"https://api.themeparks.wiki/v1/entity/{p_id}/live", timeout=15)
            data = response.json()
            
            for ride in data.get('liveData', []):
                if ride.get('entityType') == "ATTRACTION":
                    name = ride['name']
                    status = ride.get('status')
                    is_open = (status == "OPERATING")
                    
                    queue = ride.get('queue', {})
                    standby = queue.get('STANDBY', {}) if queue else {}
                    wait = standby.get('waitTime', 0) if standby else 0

                    # LOGIQUE :
                    if is_open:
                        # 1. On nettoie les anciens temps d'attente "OUVERT" pour cette attraction
                        # On ne garde que le plus frais pour ne pas saturer la base
                        supabase.table("disney_logs").delete().eq("ride_name", name).eq("is_open", True).execute()
                    
                    # 2. On insère la nouvelle donnée
                    # Si c'est fermé (is_open=False), on ne supprime rien avant : 
                    # cela va créer une suite de logs "Fermé" qui permet à l'App de calculer la durée de la panne.
                    supabase.table("disney_logs").insert({
                        "ride_name": name,
                        "wait_time": wait,
                        "is_open": is_open,
                        "created_at": datetime.utcnow().isoformat()
                    }).execute()
                        
            print(f"✅ Synchro hybride terminée pour le parc {p_id}")

        except Exception as e:
            print(f"❌ Erreur : {e}")

if __name__ == "__main__":
    run_worker()
