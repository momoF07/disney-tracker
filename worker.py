import requests
import os
from supabase import create_client
from datetime import datetime
import pytz
from config import PARK_CLOSING # On importe l'heure de fermeture

# Configuration Supabase
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

PARKS = ["dae968d5-630d-4719-8b06-3d107e944401", "ca888437-ebb4-4d50-aed2-d227f7096968"]

def run_worker():
    # --- 1. GESTION DU TEMPS (Paris) ---
    paris_tz = pytz.timezone('Europe/Paris')
    now_paris = datetime.now(paris_tz)
    current_time = now_paris.time()
    current_hour = now_paris.hour

    # --- 2. CONDITION DE GARDE : Silence de nuit (02h - 08h Paris) ---
    if 2 <= current_hour < 8:
        print(f"😴 Mode nuit (Paris). Le worker ne travaille pas entre 02:00 et 08:00.")
        return

    # --- 3. CONDITION DE GARDE : Fermeture du parc (config.py) ---
    # Si l'heure actuelle dépasse l'heure de fermeture du fichier config
    if current_time > PARK_CLOSING:
        print(f"🌙 Parc fermé (Heure de fermeture {PARK_CLOSING} dépassée). Fin des relevés.")
        return

    # --- 4. LOGIQUE DE RESET (02h00 Paris / 00h00 UTC) ---
    if current_hour == 2 and now_paris.minute < 15:
        try:
            supabase.table("disney_logs").delete().gt("id", 0).execute()
            print("🌙 Reset quotidien : Database nettoyée à 02:00.")
        except Exception as e: 
            print(f"⚠️ Erreur Reset : {e}")

    # --- 5. COLLECTE ET ÉCRITURE FORCÉE ---
    for p_id in PARKS:
        try:
            response = requests.get(f"https://api.themeparks.wiki/v1/entity/{p_id}/live", timeout=15)
            data = response.json()
            live_data = data.get('liveData', [])

            if not live_data:
                continue

            to_insert = []
            for ride in live_data:
                if ride.get('entityType') == "ATTRACTION":
                    name = ride.get('name')
                    is_open = (ride.get('status') == "OPERATING")
                    
                    queue = ride.get('queue', {})
                    standby = queue.get('STANDBY', {}) if queue else {}
                    wait = standby.get('waitTime', 0) if standby else 0

                    # On prépare l'entrée sans vérifier si c'est un doublon
                    to_insert.append({
                        "ride_name": name,
                        "wait_time": wait,
                        "is_open": is_open,
                        "created_at": datetime.now(pytz.utc).isoformat()
                    })

            # Insertion massive pour garantir la cohérence temporelle
            if to_insert:
                supabase.table("disney_logs").insert(to_insert).execute()
                print(f"✅ Synchro forcée : {len(to_insert)} attractions enregistrées pour {p_id}")

        except Exception as e:
            print(f"❌ Erreur pour le parc {p_id} : {e}")

if __name__ == "__main__":
    run_worker()
