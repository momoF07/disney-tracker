import requests
import os
from supabase import create_client
from datetime import datetime, time
import pytz
from config import PARK_OPENING, PARK_CLOSING

# --- CONFIGURATION SUPABASE ---
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

# Identifiants des parcs (DLP et DAW)
PARKS = ["dae968d5-630d-4719-8b06-3d107e944401", "ca888437-ebb4-4d50-aed2-d227f7096968"]

def run_worker():
    # --- 1. GESTION DU TEMPS (Paris) ---
    paris_tz = pytz.timezone('Europe/Paris')
    now_paris = datetime.now(paris_tz)
    current_time = now_paris.time()
    current_hour = now_paris.hour

    # --- 2. LOGIQUE DE RESET (02h00 Paris / 00h00 UTC) ---
    # On garde le reset à 2h du matin pour vider la DB avant la nouvelle journée
    if current_hour == 2 and now_paris.minute < 15:
        try:
            supabase.table("disney_logs").delete().gt("id", 0).execute()
            print("🌙 Reset quotidien : Database nettoyée à 02:00.")
        except Exception as e: 
            print(f"⚠️ Erreur Reset : {e}")

    # --- 3. SILENCE NOCTURNE DYNAMIQUE ---
    # Le worker ne travaille que si l'heure est comprise entre l'ouverture et la fermeture
    # On ajoute une petite marge de 30min avant l'ouverture pour capter les premiers flux
    marge_ouverture = (datetime.combine(datetime.today(), PARK_OPENING) - \
                      timedelta(minutes=30)).time() if 'timedelta' in globals() else PARK_OPENING

    if not (marge_ouverture <= current_time <= PARK_CLOSING):
        print(f"😴 Silence nocturne : {current_time} est en dehors des horaires {PARK_OPENING}-{PARK_CLOSING}.")
        return

    # --- 4. COLLECTE ET ÉCRITURE FORCÉE ---
    print(f"🚀 Lancement du relevé (Heure Paris : {now_paris.strftime('%H:%M')})")
    
    for p_id in PARKS:
        try:
            response = requests.get(f"https://api.themeparks.wiki/v1/entity/{p_id}/live", timeout=15)
            data = response.json()
            live_data = data.get('liveData', [])

            if not live_data:
                print(f"⚠️ Aucune donnée pour {p_id}")
                continue

            to_insert = []
            for ride in live_data:
                if ride.get('entityType') == "ATTRACTION":
                    name = ride.get('name')
                    is_open = (ride.get('status') == "OPERATING")
                    
                    queue = ride.get('queue', {})
                    standby = queue.get('STANDBY', {}) if queue else {}
                    wait = standby.get('waitTime', 0) if standby else 0

                    to_insert.append({
                        "ride_name": name,
                        "wait_time": wait,
                        "is_open": is_open,
                        "created_at": datetime.now(pytz.utc).isoformat()
                    })

            # Insertion en masse (Bulk)
            if to_insert:
                supabase.table("disney_logs").insert(to_insert).execute()
                print(f"✅ {len(to_insert)} attractions enregistrées pour {p_id}")

        except Exception as e:
            print(f"❌ Erreur pour le parc {p_id} : {e}")

if __name__ == "__main__":
    # Import nécessaire pour la marge si tu veux l'utiliser, sinon retire timedelta
    from datetime import timedelta
    run_worker()
