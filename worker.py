import requests
import os
from supabase import create_client
from datetime import datetime, time
import pytz
from config import PARK_OPENING, PARK_CLOSING, EMT_OPENING, DAW_CLOSING, DLP_CLOSING
from special_hours import ANTICIPATED_CLOSINGS, EMT_EARLY_OPEN

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

PARKS = ["dae968d5-630d-4719-8b06-3d107e944401", "ca888437-ebb4-4d50-aed2-d227f7096968"]

def get_theoretical_hours(ride_name):
    """Détermine l'ouverture et la fermeture théorique pour une attraction précise."""
    # Par défaut, on utilise les horaires globaux
    is_daw = "dae968d5" in ride_name # Logique simplifiée ou basée sur ta config
    
    # 1. Ouverture
    opening = EMT_OPENING if ride_name in EMT_EARLY_OPEN else PARK_OPENING
    
    # 2. Fermeture
    if ride_name in ANTICIPATED_CLOSINGS:
        closing = ANTICIPATED_CLOSINGS[ride_name]
    else:
        # On définit DAW_CLOSING ou DLP_CLOSING selon le parc (à adapter selon tes besoins)
        closing = PARK_CLOSING 
        
    return opening, closing

def is_ride_theoretically_open(current_time, opening, closing):
    if opening <= closing:
        return opening <= current_time <= closing
    return current_time >= opening or current_time <= closing

def run_worker():
    paris_tz = pytz.timezone('Europe/Paris')
    now_paris = datetime.now(paris_tz)
    current_time = now_paris.time()
    
    # --- 1. RESET QUOTIDIEN (02:30) ---
    if now_paris.hour == 2 and now_paris.minute < 30:
        supabase.table("daily_status").update({"has_opened_today": False}).neq("ride_name", "").execute()
        print("🌙 Reset daily_status effectué.")

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
                    
                    # --- RÉCUPÉRATION DES HORAIRES SPÉCIFIQUES ---
                    h_o, h_f = get_theoretical_hours(name)
                    theoriquement_ouvert = is_ride_theoretically_open(current_time, h_o, h_f)

                    # --- A. MISE À JOUR LIVE ---
                    supabase.table("disney_live").upsert({
                        "ride_name": name,
                        "wait_time": wait,
                        "is_open": is_open,
                        "updated_at": datetime.now(pytz.utc).isoformat()
                    }).execute()

                    # --- B. LOGIQUE PREMIÈRE OUVERTURE ---
                    has_already_opened = status_map.get(name, False)
                    if is_open and not has_already_opened:
                        supabase.table("daily_status").upsert({"ride_name": name, "has_opened_today": True}).execute()
                        has_already_opened = True

                    # --- C. LOGIQUE INCIDENTS & RETARDS (SÉCURISÉE) ---
                    active_panne_query = supabase.table("logs_101")\
                        .select("*")\
                        .eq("ride_name", name)\
                        .is_("end_time", "null")\
                        .execute()
                    
                    panne_data = active_panne_query.data

                    if not is_open:
                        # On n'enregistre un incident QUE si l'attraction est censée être ouverte
                        if theoriquement_ouvert:
                            if not panne_data:
                                supabase.table("logs_101").insert({
                                    "ride_name": name, 
                                    "start_time": datetime.now(pytz.utc).isoformat()
                                }).execute()
                                print(f"🚨 Incident/Retard : {name} (devrait être ouvert depuis {h_o})")
                    else:
                        # Si ouvert ou si l'heure de fermeture est passée, on ferme la panne
                        if panne_data:
                            incident_id = panne_data[0]['id']
                            supabase.table("logs_101").update({
                                "end_time": datetime.now(pytz.utc).isoformat()
                            }).eq("id", incident_id).execute()
                            print(f"✅ Retour normal : {name}")

            print(f"✅ Parc {p_id} traité.")
        except Exception as e:
            print(f"❌ Erreur : {e}")

if __name__ == "__main__":
    run_worker()
