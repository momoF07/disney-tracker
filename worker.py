import requests
import os
from supabase import create_client
from datetime import datetime, time
import pytz

# --- IMPORTS MODULES ---
from config import PARK_OPENING, PARK_CLOSING, EMT_OPENING, DAW_CLOSING, DLP_CLOSING
from modules.special_hours import ANTICIPATED_CLOSINGS, EMT_EARLY_OPEN
from modules.emojis import RIDES_DAW

# Configuration Supabase
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

# IDs des parcs
PARKS = ["dae968d5-630d-4719-8b06-3d107e944401", "ca888437-ebb4-4d50-aed2-d227f7096968"]

def get_theoretical_hours(ride_name):
    """Détermine l'ouverture et la fermeture théorique précise."""
    is_daw = ride_name in RIDES_DAW
    opening = EMT_OPENING if ride_name in EMT_EARLY_OPEN else PARK_OPENING
    
    if ride_name in ANTICIPATED_CLOSINGS:
        closing = ANTICIPATED_CLOSINGS[ride_name]
    else:
        closing = DAW_CLOSING if is_daw else DLP_CLOSING
        
    return opening, closing

def is_ride_theoretically_open(current_time, opening, closing):
    if opening <= closing:
        return opening <= current_time <= closing
    return current_time >= opening or current_time <= closing

def run_worker():
    paris_tz = pytz.timezone('Europe/Paris')
    now_paris = datetime.now(paris_tz)
    current_time = now_paris.time()
    current_day = now_paris.strftime('%Y-%m-%d')

    # --- 1. RESET & SYNC DES HORAIRES PARCS (via /schedule) ---
    if now_paris.hour == 2 and now_paris.minute < 30:
        supabase.table("daily_status").update({"has_opened_today": False}).neq("ride_name", "").execute()
        
        for p_id in PARKS:
            try:
                res = requests.get(f"https://api.themeparks.wiki/v1/entity/{p_id}/schedule")
                for entry in res.json().get('schedules', []):
                    if entry.get('date') == current_day and entry.get('type') == 'OPERATING':
                        o_time = entry['openingTime'].split('T')[1][:5]
                        c_time = entry['closingTime'].split('T')[1][:5]
                        supabase.table("ride_schedules").upsert({
                            "ride_name": "Disneyland Park" if "dae9" in p_id else "Adventure World",
                            "opening_time": o_time,
                            "closing_time": c_time,
                            "type": "PARK",
                            "updated_at": "now()"
                        }).execute()
            except Exception as e: print(f"❌ Erreur Schedule: {e}")

    # --- 2. TRAITEMENT LIVE (Attractions + Shows) ---
    status_db = supabase.table("daily_status").select("*").execute()
    status_map = {item['ride_name']: item['has_opened_today'] for item in status_db.data}

    for p_id in PARKS:
        try:
            response = requests.get(f"https://api.themeparks.wiki/v1/entity/{p_id}/live", timeout=15)
            live_data = response.json().get('liveData', [])

            for item in live_data:
                name = item.get('name')
                
                # --- A. CAS DES SPECTACLES (SHOW) ---
                if item.get('entityType') == "SHOW":
                    showtimes = item.get('showtimes', [])
                    for stime in showtimes:
                        # On ne garde que les shows de la journée
                        if stime.get('startTime', '').startswith(current_day):
                            start = stime.get('startTime').split('T')[1][:5]
                            supabase.table("ride_schedules").upsert({
                                "ride_name": name,
                                "opening_time": start,
                                "type": "SHOW",
                                "updated_at": "now()"
                            }).execute()

                # --- B. CAS DES ATTRACTIONS ---
                elif item.get('entityType') == "ATTRACTION":
                    is_open = (item.get('status') == "OPERATING")
                    wait = item.get('queue', {}).get('STANDBY', {}).get('waitTime', 0)
                    h_o, h_f = get_theoretical_hours(name)
                    theoriquement_ouvert = is_ride_theoretically_open(current_time, h_o, h_f)

                    # Mise à jour Live
                    supabase.table("disney_live").upsert({
                        "ride_name": name, "wait_time": wait, "is_open": is_open, "updated_at": "now()"
                    }).execute()

                    # Gestion première ouverture
                    if is_open and not status_map.get(name, False):
                        supabase.table("daily_status").upsert({"ride_name": name, "has_opened_today": True}).execute()

                    # Logs Incidents (101)
                    active_panne = supabase.table("logs_101").select("*").eq("ride_name", name).is_("end_time", "null").execute().data
                    if not is_open and theoriquement_ouvert and not active_panne:
                        supabase.table("logs_101").insert({"ride_name": name, "start_time": "now()"}).execute()
                    elif is_open and active_panne:
                        supabase.table("logs_101").update({"end_time": "now()"}).eq("id", active_panne[0]['id']).execute()

            print(f"✅ Parc {p_id} traité.")
        except Exception as e: print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    run_worker()