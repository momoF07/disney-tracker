import requests
import os
from supabase import create_client
from datetime import datetime
import pytz

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

PARKS = ["dae968d5-630d-4719-8b06-3d107e944401", "ca888437-ebb4-4d50-aed2-d227f7096968"]

def run_worker():
    # --- LOGIQUE DE RESET À 2H DU MATIN (PARIS) ---
    paris_tz = pytz.timezone('Europe/Paris')
    now_paris = datetime.now(paris_tz)
    
    # Si on est entre 01:00 et 01:15, on vide la table proprement
    if now_paris.hour == 1 and now_paris.minute < 15:
        try:
            # On utilise RPC pour lancer une commande SQL TRUNCATE si possible
            # Sinon, on delete tout (le TRUNCATE est préférable via le SQL Editor une fois)
            supabase.table("disney_logs").delete().gt("id", 0).execute()
            print("🌙 Reset de nuit effectué : Base vidée.")
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

                    # Si ouvert : on supprime l'ancien record "ouvert" pour ne garder que le dernier temps
                    if is_open:
                        supabase.table("disney_logs").delete().eq("ride_name", name).eq("is_open", True).execute()
                    
                    # On insère le nouveau record (toujours si fermé, remplace si ouvert)
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
