import requests
import os
from supabase import create_client

# On récupère les IDs via l'environnement GitHub
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

# Les 2 parcs (DLP + DAW)
PARKS = ["dae968d5-630d-4719-8b06-3d107e944401", "ca888437-ebb4-4d50-aed2-d227f7096968"]
# Ajoute simplement les noms exacts ici (ceux que tu as vus dans le scanner)
TARGETS = [
    "Big Thunder Mountain", 
    "Phantom Manor", 
]

for p_id in PARKS:
    try:
        response = requests.get(f"https://api.themeparks.wiki/v1/entity/{p_id}/live", timeout=10)
        data = response.json()
        for ride in data.get('liveData', []):
            # On enregistre TOUT ce qui est une attraction (pas les restos/boutiques)
            if ride.get('entityType') == "ATTRACTION":
                supabase.table("disney_logs").insert({
                    "ride_name": ride['name'],
                    "wait_time": ride.get('queue', {}).get('STANDBY', {}).get('waitTime', 0),
                    "is_open": ride['status'] == "OPERATING"
                }).execute()
    except Exception as e:
        print(f"Erreur : {e}")
