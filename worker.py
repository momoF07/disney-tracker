import requests
import os
from supabase import create_client
from datetime import datetime, timedelta

# Configuration Supabase
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

# IDs des Parcs
PARKS = ["dae968d5-630d-4719-8b06-3d107e944401", "ca888437-ebb4-4d50-aed2-d227f7096968"]

def run_worker():
    # 1. Nettoyage des vieux logs (> 24h) pour garder la base légère
    try:
        hier = (datetime.utcnow() - timedelta(days=1)).isoformat()
        supabase.table("disney_logs").delete().lt("created_at", hier).execute()
        print("🧹 Nettoyage des anciens logs effectué.")
    except Exception as e:
        print(f"Erreur nettoyage : {e}")

    # 2. Récupération et Insertion
    all_logs = []
    for p_id in PARKS:
        try:
            response = requests.get(f"https://api.themeparks.wiki/v1/entity/{p_id}/live", timeout=15)
            data = response.json()
            
            for ride in data.get('liveData', []):
                if ride.get('entityType') == "ATTRACTION":
                    queue = ride.get('queue', {})
                    standby = queue.get('STANDBY', {}) if queue else {}
                    
                    all_logs.append({
                        "ride_name": ride['name'],
                        "wait_time": standby.get('waitTime', 0) if standby else 0,
                        "is_open": ride['status'] == "OPERATING",
                        "created_at": datetime.utcnow().isoformat()
                    })
        except Exception as e:
            print(f"Erreur parc {p_id}: {e}")

    # 3. Envoi groupé à Supabase
    if all_logs:
        try:
            supabase.table("disney_logs").insert(all_logs).execute()
            print(f"🚀 {len(all_logs)} logs insérés avec succès.")
        except Exception as e:
            print(f"Erreur insertion : {e}")

if __name__ == "__main__":
    run_worker()
