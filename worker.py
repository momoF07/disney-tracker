import requests
import os
from supabase import create_client
from datetime import datetime
import pytz

# Configuration Supabase
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

PARKS = ["dae968d5-630d-4719-8b06-3d107e944401", "ca888437-ebb4-4d50-aed2-d227f7096968"]

def run_worker():
    # --- 1. GESTION DU TEMPS (Fuseau Paris) ---
    paris_tz = pytz.timezone('Europe/Paris')
    now_paris = datetime.now(paris_tz)
    current_hour = now_paris.hour

    # --- 2. CONDITION DE GARDE : Silence de nuit (02h - 08h) ---
    if 2 <= current_hour < 8:
        print(f"😴 Mode nuit activé ({current_hour}h). Le worker reste au lit.")
        return

    # --- LOGIQUE DE RESET (02h00 Paris) ---
    if current_hour == 2 and now_paris.minute < 15:
        try:
            supabase.table("disney_logs").delete().gt("id", 0).execute()
            print("🌙 Database nettoyée pour la nouvelle journée.")
        except Exception as e: print(f"Erreur Reset : {e}")

    # --- COLLECTE DES DONNÉES ---
    for p_id in PARKS:
        try:
            response = requests.get(f"https://api.themeparks.wiki/v1/entity/{p_id}/live", timeout=15)
            data = response.json()
            live_data = data.get('liveData', [])

            # --- 3. CONDITION DE GARDE : Arrêt si tout est fermé (Fin de journée) ---
            # On vérifie si au moins UNE attraction est ouverte dans le parc
            any_ride_open = any(ride.get('status') == "OPERATING" for ride in live_data if ride.get('entityType') == "ATTRACTION")
            
            # Si tout est fermé ET qu'il est tard (ex: après 19h), on arrête d'écrire.
            # Cela permet à l'App Streamlit de détecter que 'tous_fermes_globalement' est vrai.
            if not any_ride_open and current_hour >= 19:
                print(f"🌙 Toutes les attractions sont fermées ({p_id}). Fin des relevés pour aujourd'hui.")
                continue

            for ride in live_data:
                if ride.get('entityType') == "ATTRACTION":
                    name = ride['name']
                    is_open = (ride.get('status') == "OPERATING")
                    
                    queue = ride.get('queue', {})
                    standby = queue.get('STANDBY', {}) if queue else {}
                    wait = standby.get('waitTime', 0) if standby else 0

                    # --- 4. RÉCUPÉRATION DU DERNIER ÉTAT ---
                    last_record = supabase.table("disney_logs")\
                        .select("wait_time, is_open")\
                        .eq("ride_name", name)\
                        .order("created_at", desc=True)\
                        .limit(1).execute()

                    # --- 5. LOGIQUE DÉCISIONNELLE ---
                    should_write = True
                    
                    # Garde Matinale : Si fermé et n'a jamais ouvert aujourd'hui -> On ignore
                    if not last_record.data and not is_open:
                        continue

                    if last_record.data:
                        last_wait = last_record.data[0]['wait_time']
                        last_open = last_record.data[0]['is_open']
                        
                        # Si ouvert et rien n'a changé : On n'écrit pas (économie de lignes)
                        if is_open and last_open == is_open and last_wait == wait:
                            should_write = False
                        
                        # Si l'attraction est fermée (panne) : On écrit (Heartbeat pour éviter l'addition des pannes)
                        elif not is_open:
                            should_write = True

                    if should_write:
                        # Nettoyage des records "Ouvert" pour ne garder que le dernier
                        if is_open:
                            supabase.table("disney_logs").delete().eq("ride_name", name).eq("is_open", True).execute()
                        
                        # Insertion du nouvel état
                        supabase.table("disney_logs").insert({
                            "ride_name": name,
                            "wait_time": wait,
                            "is_open": is_open,
                            "created_at": datetime.now(pytz.utc).isoformat()
                        }).execute()
                        
            print(f"✅ Synchro OK pour {p_id}")
        except Exception as e:
            print(f"❌ Erreur : {e}")

if __name__ == "__main__":
    run_worker()
