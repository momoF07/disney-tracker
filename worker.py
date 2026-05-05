import requests
import os
from supabase import create_client
from datetime import datetime
import pytz

from config import PARK_OPENING, PARK_CLOSING, EMT_OPENING, DAW_CLOSING, DLP_CLOSING
from modules.special_hours import ANTICIPATED_CLOSINGS, EMT_EARLY_OPEN
from modules.emojis import RIDES_DAW

# Configuration Supabase
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

PARKS = ["dae968d5-630d-4719-8b06-3d107e944401", "ca888437-ebb4-4d50-aed2-d227f7096968"]

def get_theoretical_hours(ride_name):
    """Retourne (heure_ouverture, heure_fermeture) théoriques pour une attraction."""
    from datetime import time

    # Fermetures anticipées spécifiques
    if ride_name in ANTICIPATED_CLOSINGS:
        closing = ANTICIPATED_CLOSINGS[ride_name]
    elif ride_name in RIDES_DAW:
        closing = DAW_CLOSING
    else:
        closing = DLP_CLOSING

    # Ouverture EMT anticipée
    if ride_name in EMT_EARLY_OPEN:
        opening = EMT_OPENING
    else:
        opening = PARK_OPENING

    return opening, closing

def is_ride_theoretically_open(current_time, opening, closing):
    """Vérifie si une attraction devrait être ouverte à l'heure actuelle."""
    if opening is None or closing is None:
        return False
    return opening <= current_time <= closing

def run_worker():
    print("⏳ [WORKER] Actualisation des attractions...")
    paris_tz = pytz.timezone('Europe/Paris')
    now_paris = datetime.now(paris_tz)
    current_time = now_paris.time()

    # --- RESET QUOTIDIEN ---
    if now_paris.hour == 2 and now_paris.minute < 30:
        supabase.table("daily_status").update({"has_opened_today": False}).neq("ride_name", "").execute()

    # Statut pour détection de pannes
    status_db = supabase.table("daily_status").select("*").execute()
    status_map = {item['ride_name']: item['has_opened_today'] for item in status_db.data}

    for p_id in PARKS:
        try:
            response = requests.get(f"https://api.themeparks.wiki/v1/entity/{p_id}/live", timeout=15)
            live_data = response.json().get('liveData', [])

            for item in live_data:
                # UNQUEMENT LES ATTRACTIONS
                if item.get('entityType') == "ATTRACTION":
                    name = item.get('name')
                    is_open = (item.get('status') == "OPERATING")
                    wait = item.get('queue', {}).get('STANDBY', {}).get('waitTime', 0)
                    
                    h_o, h_f = get_theoretical_hours(name)
                    theoriquement_ouvert = is_ride_theoretically_open(current_time, h_o, h_f)

                    # 1. Update Table Live
                    supabase.table("disney_live").upsert({
                        "ride_name": name, 
                        "wait_time": wait, 
                        "is_open": is_open, 
                        "updated_at": datetime.now().isoformat()
                    }).execute()

                    # 2. Détection Première Ouverture
                    if is_open and not status_map.get(name, False):
                        supabase.table("daily_status").upsert({"ride_name": name, "has_opened_today": True}).execute()

                    # 3. Logs Incidents (101)
                    active_panne = supabase.table("logs_101").select("*").eq("ride_name", name).is_("end_time", "null").execute().data
                    if not is_open and theoriquement_ouvert and not active_panne:
                        supabase.table("logs_101").insert({"ride_name": name, "start_time": datetime.now().isoformat()}).execute()
                    elif is_open and active_panne:
                        supabase.table("logs_101").update({"end_time": datetime.now().isoformat()}).eq("id", active_panne[0]['id']).execute()

            print(f"✅ [WORKER] Parc {p_id} actualisé.")
        except Exception as e:
            print(f"❌ Erreur Worker: {e}")

if __name__ == "__main__":
    run_worker()