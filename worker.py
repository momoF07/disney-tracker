import requests
import os
from supabase import create_client
from datetime import datetime
import pytz
from config import PARK_OPENING, PARK_CLOSING

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

PARKS = ["dae968d5-630d-4719-8b06-3d107e944401", "ca888437-ebb4-4d50-aed2-d227f7096968"]

def is_park_theoretically_open(current, opening, closing):
    if opening <= closing: return opening <= current <= closing
    return current >= opening or current <= closing

def run_worker():
    paris_tz = pytz.timezone('Europe/Paris')
    now_paris = datetime.now(paris_tz)
    current_time = now_paris.time()
    
    # Reset quotidien (uniquement pour daily_status et logs_101 si besoin)
    if now_paris.hour == 2 and now_paris.minute < 30:
        supabase.table("daily_status").update({"has_opened_today": False}).neq("ride_name", "").execute()
        print("🌙 Reset daily_status effectué.")

    if not is_park_theoretically_open(current_time, PARK_OPENING, PARK_CLOSING):
        return

    # Récupération des statuts d'ouverture
    status_db = supabase.table("daily_status").select("*").execute()
    status_map = {item['ride_name']: item['has_opened_today'] for item in status_db.data}

    for p_id in PARKS:
        try:
            response = requests.get(f"https://api.themeparks.wiki/v1/entity/{p_id}/live", timeout=15)
            live_data = response.json().get('liveData', [])

            for ride in live_data:
                if ride.get('entityType') == "ATTRACTION":
                    name = ride.get('name')
                    is_open = (ride.get('status') == "OPERATING")
                    wait = ride.get('queue', {}).get('STANDBY', {}).get('waitTime', 0)

                    # A. MISE À JOUR LIVE (Ligne unique par attraction)
                    supabase.table("disney_live").upsert({
                        "ride_name": name,
                        "wait_time": wait,
                        "is_open": is_open,
                        "updated_at": datetime.now(pytz.utc).isoformat()
                    }).execute()

                    # B. LOGIQUE OUVERTURE (daily_status)
                    has_already_opened = status_map.get(name, False)
                    if is_open and not has_already_opened:
                        supabase.table("daily_status").upsert({"ride_name": name, "has_opened_today": True}).execute()
                        has_already_opened = True

                    # C. LOGIQUE PANNES (logs_101)
                    if has_already_opened:
                        last_panne = supabase.table("logs_101").select("*").eq("ride_name", name).is_("end_time", "null").execute()
                        if not is_open and not last_panne.data:
                            supabase.table("logs_101").insert({"ride_name": name, "start_time": datetime.now(pytz.utc).isoformat()}).execute()
                        elif is_open and last_panne.data:
                            supabase.table("logs_101").update({"end_time": datetime.now(pytz.utc).isoformat()}).eq("id", last_panne.data[0]['id']).execute()

            print(f"✅ Mise à jour Live terminée pour {p_id}")
        except Exception as e:
            print(f"❌ Erreur : {e}")

if __name__ == "__main__":
    run_worker()
