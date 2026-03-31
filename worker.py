import requests
import os
from supabase import create_client
from datetime import datetime # <--- AJOUTÉ

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

PARKS = ["dae968d5-630d-4719-8b06-3d107e944401", "ca888437-ebb4-4d50-aed2-d227f7096968"]

for p_id in PARKS:
    try:
        response = requests.get(f"https://api.themeparks.wiki/v1/entity/{p_id}/live", timeout=15)
        data = response.json()
        
        logs = [] # On prépare une liste pour envoyer tout d'un coup (plus rapide)
        
        for ride in data.get('liveData', []):
            if ride.get('entityType') == "ATTRACTION":
                # On récupère le temps d'attente (gestion des None/0)
                queue = ride.get('queue', {})
                standby = queue.get('STANDBY', {}) if queue else {}
                wait = standby.get('waitTime', 0) if standby else 0
                
                logs.append({
                    "ride_name": ride['name'],
                    "wait_time": wait,
                    "is_open": ride['status'] == "OPERATING",
                    "created_at": datetime.utcnow().isoformat() # <--- FORCE L'HEURE UTC
                })
        
        # Insertion groupée (Batch insert) : plus stable et évite les erreurs de timeout
        if logs:
            supabase.table("disney_logs").insert(logs).execute()
            print(f"✅ {len(logs)} attractions mises à jour pour le parc {p_id}")

    except Exception as e:
        print(f"❌ Erreur pour le parc {p_id} : {e}")
