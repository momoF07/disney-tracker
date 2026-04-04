import requests
import os
from supabase import create_client
from datetime import datetime, timedelta
import pytz
from config import PARK_OPENING, PARK_CLOSING

# --- CONFIGURATION SUPABASE ---
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

# Identifiants des parcs (DLP et DAW)
PARKS = ["dae968d5-630d-4719-8b06-3d107e944401", "ca888437-ebb4-4d50-aed2-d227f7096968"]

def is_park_theoretically_open(current, opening, closing):
    """
    Vérifie si l'heure actuelle est dans la plage d'ouverture.
    Gère le cas où la fermeture est après minuit (ex: 02:00).
    """
    if opening <= closing:
        # Cas standard : 08:15 -> 23:00
        return opening <= current <= closing
    else:
        # Cas nocturne : 08:15 -> 02:00 (le lendemain)
        return current >= opening or current <= closing

def run_worker():
    # --- 1. GESTION DU TEMPS (Paris) ---
    paris_tz = pytz.timezone('Europe/Paris')
    now_paris = datetime.now(paris_tz)
    current_time = now_paris.time()
    current_hour = now_paris.hour

    # --- 2. LOGIQUE DE RESET (Décalée à 04h00) ---
    # On vide la DB quand le parc est GARANTI fermé, même en cas de soirée spéciale.
    if current_hour == 4 and now_paris.minute < 15:
        try:
            supabase.table("disney_logs").delete().gt("id", 0).execute()
            print("🌙 Reset quotidien : Database nettoyée à 04:00.")
        except Exception as e: 
            print(f"⚠️ Erreur Reset : {e}")

    # --- 3. SILENCE NOCTURNE DYNAMIQUE ---
    # On vérifie si on est dans la plage horaire définie dans config.py
    if not is_park_theoretically_open(current_time, PARK_OPENING, PARK_CLOSING):
        print(f"😴 Silence nocturne : {current_time} est hors créneau ({PARK_OPENING} - {PARK_CLOSING}).")
        return

    # --- 4. COLLECTE ET ÉCRITURE SYSTÉMATIQUE ---
    print(f"🚀 Lancement du relevé (Heure Paris : {now_paris.strftime('%H:%M')})")
    
    for p_id in PARKS:
        try:
            response = requests.get(f"https://api.themeparks.wiki/v1/entity/{p_id}/live", timeout=15)
            data = response.json()
            live_data = data.get('liveData', [])

            if not live_data:
                print(f"⚠️ Aucune donnée reçue pour le parc {p_id}")
                continue

            to_insert = []
            for ride in live_data:
                if ride.get('entityType') == "ATTRACTION":
                    name = ride.get('name')
                    status = ride.get('status')
                    is_open = (status == "OPERATING")
                    
                    queue = ride.get('queue', {})
                    standby = queue.get('STANDBY', {}) if queue else {}
                    wait = standby.get('waitTime', 0) if standby else 0

                    to_insert.append({
                        "ride_name": name,
                        "wait_time": wait,
                        "is_open": is_open,
                        "created_at": datetime.now(pytz.utc).isoformat()
                    })

            # Insertion en masse (Bulk Insert) pour plus de fiabilité
            if to_insert:
                supabase.table("disney_logs").insert(to_insert).execute()
                print(f"✅ {len(to_insert)} attractions enregistrées pour {p_id}")

        except Exception as e:
            print(f"❌ Erreur critique pour le parc {p_id} : {e}")

if __name__ == "__main__":
    run_worker()
