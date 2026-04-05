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
    """Gère l'amplitude horaire, même après minuit."""
    if opening <= closing:
        return opening <= current <= closing
    return current >= opening or current <= closing

def run_worker():
    # --- 1. GESTION DU TEMPS (Paris) ---
    paris_tz = pytz.timezone('Europe/Paris')
    now_paris = datetime.now(paris_tz)
    current_time = now_paris.time()
    current_hour = now_paris.hour

    # --- 2. LOGIQUE DE RESET (02h30) ---
    if current_hour == 2 and now_paris.minute < 30:
        try:
            # On vide les logs live
            supabase.table("disney_logs").delete().gt("id", 0).execute()
            # On réinitialise les statuts d'ouverture quotidienne
            supabase.table("daily_status").update({"has_opened_today": False}).neq("ride_name", "").execute()
            print("🌙 Reset quotidien : disney_logs et daily_status nettoyés.")
        except Exception as e: 
            print(f"⚠️ Erreur Reset : {e}")

    # --- 3. SILENCE NOCTURNE DYNAMIQUE ---
    if not is_park_theoretically_open(current_time, PARK_OPENING, PARK_CLOSING):
        print(f"😴 Silence nocturne : {current_time} est hors créneau.")
        return

    # --- 4. COLLECTE ET ÉCRITURE ---
    print(f"🚀 Lancement du relevé ({now_paris.strftime('%H:%M')})")
    
    # Récupération de tous les statuts d'ouverture en une fois pour gagner du temps
    status_db = supabase.table("daily_status").select("*").execute()
    status_map = {item['ride_name']: item['has_opened_today'] for item in status_db.data}

    for p_id in PARKS:
        try:
            response = requests.get(f"https://api.themeparks.wiki/v1/entity/{p_id}/live", timeout=15)
            data = response.json()
            live_data = data.get('liveData', [])

            if not live_data: continue

            to_insert_live = []
            
            for ride in live_data:
                if ride.get('entityType') == "ATTRACTION":
                    name = ride.get('name')
                    status = ride.get('status')
                    is_open = (status == "OPERATING")
                    
                    queue = ride.get('queue', {})
                    wait = queue.get('STANDBY', {}).get('waitTime', 0) if queue else 0

                    # A. Préparation Live Data
                    to_insert_live.append({
                        "ride_name": name,
                        "wait_time": wait,
                        "is_open": is_open,
                        "created_at": datetime.now(pytz.utc).isoformat()
                    })

                    # B. Gestion du Statut d'Ouverture (daily_status)
                    has_already_opened = status_map.get(name, False)

                    if is_open and not has_already_opened:
                        # Première ouverture détectée !
                        supabase.table("daily_status").upsert({
                            "ride_name": name,
                            "has_opened_today": True,
                            "last_opening_time": datetime.now(pytz.utc).isoformat()
                        }).execute()
                        has_already_opened = True
                        print(f"✨ {name} a ouvert pour la première fois aujourd'hui.")

                    # C. Gestion des Pannes (logs_101)
                    # On ne logue un incident QUE si l'attraction a déjà ouvert au moins une fois
                    if has_already_opened:
                        last_incident = supabase.table("logs_101")\
                            .select("*")\
                            .eq("ride_name", name)\
                            .is_("end_time", "null")\
                            .execute()

                        if not is_open:
                            # Début de panne
                            if not last_incident.data:
                                supabase.table("logs_101").insert({
                                    "ride_name": name,
                                    "start_time": datetime.now(pytz.utc).isoformat()
                                }).execute()
                                print(f"🚨 LOG_101 : Panne sur {name}")
                        else:
                            # Fin de panne
                            if last_incident.data:
                                incident_id = last_incident.data[0]['id']
                                supabase.table("logs_101").update({
                                    "end_time": datetime.now(pytz.utc).isoformat()
                                }).eq("id", incident_id).execute()
                                print(f"✅ LOG_101 : {name} a rouvert")

            # Bulk Insert Live
            if to_insert_live:
                supabase.table("disney_logs").insert(to_insert_live).execute()

        except Exception as e:
            print(f"❌ Erreur parc {p_id} : {e}")

if __name__ == "__main__":
    run_worker()
