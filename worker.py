import requests
import os
from supabase import create_client
from datetime import datetime, time
import pytz

# --- CORRECTION DES IMPORTS (Pointent vers les nouveaux dossiers) ---
from config import PARK_OPENING, PARK_CLOSING, EMT_OPENING, DAW_CLOSING, DLP_CLOSING
from modules.special_hours import ANTICIPATED_CLOSINGS, EMT_EARLY_OPEN
from modules.emojis import RIDES_DAW

# Configuration Supabase via variables d'environnement (GitHub Actions)
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

# IDs des parcs Disneyland Park et Disney Adventure World
PARKS = ["dae968d5-630d-4719-8b06-3d107e944401", "ca888437-ebb4-4d50-aed2-d227f7096968"]

def get_theoretical_hours(ride_name):
    """Détermine l'ouverture et la fermeture théorique précise pour chaque attraction."""
    # 1. Identification du parc pour la fermeture standard
    is_daw = ride_name in RIDES_DAW
    
    # 2. Heure d'ouverture (EMT ou Standard)
    opening = EMT_OPENING if ride_name in EMT_EARLY_OPEN else PARK_OPENING
    
    # 3. Heure de fermeture (Anticipée ou Standard du parc)
    if ride_name in ANTICIPATED_CLOSINGS:
        closing = ANTICIPATED_CLOSINGS[ride_name]
    else:
        closing = DAW_CLOSING if is_daw else DLP_CLOSING
        
    return opening, closing

def is_ride_theoretically_open(current_time, opening, closing):
    """Vérifie si l'heure actuelle est comprise dans la plage d'ouverture."""
    if opening <= closing:
        return opening <= current_time <= closing
    # Gestion des parcs fermant après minuit (rare mais possible)
    return current_time >= opening or current_time <= closing

def run_worker():
    paris_tz = pytz.timezone('Europe/Paris')
    now_paris = datetime.now(paris_tz)
    current_time = now_paris.time()
    
    # --- 1. RESET QUOTIDIEN (02:30 AM) ---
    if now_paris.hour == 2 and now_paris.minute < 30:
        supabase.table("daily_status").update({"has_opened_today": False}).neq("ride_name", "").execute()
        print("🌙 Reset quotidien des statuts effectué.")

    # Récupération de l'état "a déjà ouvert aujourd'hui" pour la logique de retard
    status_db = supabase.table("daily_status").select("*").execute()
    status_map = {item['ride_name']: item['has_opened_today'] for item in status_db.data}

    for p_id in PARKS:
        try:
            # Récupération des données Live via API Themeparks Wiki
            response = requests.get(f"https://api.themeparks.wiki/v1/entity/{p_id}/live", timeout=15)
            live_data = response.json().get('liveData', [])

            for ride in live_data:
                if ride.get('entityType') == "ATTRACTION":
                    name = ride.get('name')
                    is_open = (ride.get('status') == "OPERATING")
                    wait = ride.get('queue', {}).get('STANDBY', {}).get('waitTime', 0)
                    
                    # Récupération des horaires théoriques (config + special_hours)
                    h_o, h_f = get_theoretical_hours(name)
                    theoriquement_ouvert = is_ride_theoretically_open(current_time, h_o, h_f)

                    # --- A. MISE À JOUR TABLE LIVE ---
                    supabase.table("disney_live").upsert({
                        "ride_name": name,
                        "wait_time": wait,
                        "is_open": is_open,
                        "updated_at": datetime.now(pytz.utc).isoformat()
                    }).execute()

                    # --- B. DÉTECTION PREMIÈRE OUVERTURE DU JOUR ---
                    if is_open and not status_map.get(name, False):
                        supabase.table("daily_status").upsert({"ride_name": name, "has_opened_today": True}).execute()
                        status_map[name] = True # Mise à jour locale

                    # --- C. GESTION DES LOGS D'INCIDENTS (101) ---
                    # On vérifie s'il existe une panne déjà active (end_time est NULL)
                    active_panne_query = supabase.table("logs_101")\
                        .select("*")\
                        .eq("ride_name", name)\
                        .is_("end_time", "null")\
                        .execute()
                    
                    panne_active = active_panne_query.data

                    if not is_open:
                        # Si l'attraction est fermée alors qu'elle devrait être ouverte : on log
                        if theoriquement_ouvert:
                            if not panne_active:
                                supabase.table("logs_101").insert({
                                    "ride_name": name, 
                                    "start_time": datetime.now(pytz.utc).isoformat()
                                }).execute()
                                print(f"🚨 INCIDENT : {name} est fermé (théoriquement ouvert depuis {h_o})")
                    else:
                        # Si l'attraction est ouverte mais qu'une panne était enregistrée : on la ferme
                        if panne_active:
                            incident_id = panne_active[0]['id']
                            supabase.table("logs_101").update({
                                "end_time": datetime.now(pytz.utc).isoformat()
                            }).eq("id", incident_id).execute()
                            print(f"✅ RETOUR NORMAL : {name}")

            print(f"✅ Parc {p_id} traité avec succès.")
        except Exception as e:
            print(f"❌ Erreur lors du traitement du parc {p_id} : {e}")

if __name__ == "__main__":
    run_worker()