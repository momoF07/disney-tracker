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
        return opening <= current <= closing
    else:
        return current >= opening or current <= closing

def run_worker():
    # --- 1. GESTION DU TEMPS (Paris) ---
    paris_tz = pytz.timezone('Europe/Paris')
    now_paris = datetime.now(paris_tz)
    current_time = now_paris.time()
    current_hour = now_paris.hour
    
    # Seuil de reset pour vérifier si l'attraction a ouvert aujourd'hui
    reset_time_today = now_paris.replace(hour=2, minute=30, second=0, microsecond=0).isoformat()

    # --- 2. LOGIQUE DE RESET (02h30) ---
    if current_hour == 2 and now_paris.minute < 30:
        try:
            supabase.table("disney_logs").delete().gt("id", 0).execute()
            print("🌙 Reset quotidien : Database disney_logs nettoyée.")
        except Exception as e: 
            print(f"⚠️ Erreur Reset : {e}")

    # --- 3. SILENCE NOCTURNE DYNAMIQUE ---
    if not is_park_theoretically_open(current_time, PARK_OPENING, PARK_CLOSING):
        print(f"😴 Silence nocturne : {current_time} est hors créneau ({PARK_OPENING} - {PARK_CLOSING}).")
        return

    # --- 4. COLLECTE ET ÉCRITURE ---
    print(f"🚀 Lancement du relevé (Heure Paris : {now_paris.strftime('%H:%M')})")
    
    for p_id in PARKS:
        try:
            response = requests.get(f"https://api.themeparks.wiki/v1/entity/{p_id}/live", timeout=15)
            data = response.json()
            live_data = data.get('liveData', [])

            if not live_data:
                print(f"⚠️ Aucune donnée reçue pour le parc {p_id}")
                continue

            to_insert_live = []
            
            for ride in live_data:
                if ride.get('entityType') == "ATTRACTION":
                    name = ride.get('name')
                    status = ride.get('status')
                    is_open = (status == "OPERATING")
                    
                    queue = ride.get('queue', {})
                    standby = queue.get('STANDBY', {}) if queue else {}
                    wait = standby.get('waitTime', 0) if standby else 0

                    # A. Préparation pour disney_logs (Live)
                    to_insert_live.append({
                        "ride_name": name,
                        "wait_time": wait,
                        "is_open": is_open,
                        "created_at": datetime.now(pytz.utc).isoformat()
                    })

                    # B. LOGIQUE GESTION DES PANNES (logs_101)
                    
                    # 1. Vérification robuste de l'ouverture précédente
                    has_opened_today = False
                    if is_open:
                        has_opened_today = True
                    else:
                        # On utilise count="exact" pour une réponse fiable de la DB
                        check_db = supabase.table("disney_logs")\
                            .select("id", count="exact")\
                            .eq("ride_name", name)\
                            .eq("is_open", True)\
                            .gte("created_at", reset_time_today)\
                            .limit(1)\
                            .execute()
                        has_opened_today = (check_db.count is not None and check_db.count > 0)

                    # 2. Gestion de la table logs_101
                    if has_opened_today:
                        # On cherche une panne non terminée (end_time is NULL)
                        last_incident = supabase.table("logs_101")\
                            .select("*")\
                            .eq("ride_name", name)\
                            .is_("end_time", "null")\
                            .execute()

                        if not is_open:
                            # Début de panne : pas d'incident ouvert trouvé
                            if not last_incident.data:
                                supabase.table("logs_101").insert({
                                    "ride_name": name,
                                    "start_time": datetime.now(pytz.utc).isoformat()
                                }).execute()
                                print(f"🚨 LOG_101 : Début d'interruption pour {name}")
                        else:
                            # Fin de panne : on ferme l'incident avec end_time
                            if last_incident.data:
                                incident_id = last_incident.data[0]['id']
                                supabase.table("logs_101").update({
                                    "end_time": datetime.now(pytz.utc).isoformat()
                                }).eq("id", incident_id).execute()
                                print(f"✅ LOG_101 : Réouverture de {name}")

            # Insertion Bulk dans disney_logs (pour le graph et le live)
            if to_insert_live:
                supabase.table("disney_logs").insert(to_insert_live).execute()
                print(f"✅ Relevé live inséré pour {p_id}")

        except Exception as e:
            print(f"❌ Erreur critique pour le parc {p_id} : {e}")

if __name__ == "__main__":
    run_worker()
