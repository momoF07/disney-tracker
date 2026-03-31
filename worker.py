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
    # --- LOGIQUE DE RESET (Cible : 02h00 - 02h20 Paris) ---
    now_utc = datetime.utcnow()
    
    # 00h UTC (Eté) ou 01h UTC (Hiver) et dans les 20 premières minutes
    if now_utc.hour in [0, 1] and now_utc.minute < 20:
        try:
            # On vide la table pour recommencer la journée à neuf
            supabase.table("disney_logs").delete().gt("id", 0).execute()
            print(f"🌙 Reset de nuit effectué à {now_utc.hour}:{now_utc.minute} UTC")
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

                    # 1. Si ouvert : on supprime l'ancien record "ouvert" pour cette attraction
                    if is_open:
                        supabase.table("disney_logs").delete().eq("ride_name", name).eq("is_open", True).execute()
                    
                    # 2. On insère la nouvelle donnée (Temps actuel ou signalement de panne)
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
