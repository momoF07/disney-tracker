import requests
import os
from supabase import create_client
from datetime import datetime

# Configuration Supabase
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

PARKS = ["dae968d5-630d-4719-8b06-3d107e944401", "ca888437-ebb4-4d50-aed2-d227f7096968"]

def run_worker():
    # --- LOGIQUE DE RESET (Inchangée) ---
    now_utc = datetime.utcnow()
    if now_utc.hour in [0, 1] and now_utc.minute < 20:
        try:
            supabase.table("disney_logs").delete().gt("id", 0).execute()
            print(f"🌙 Reset de nuit effectué.")
        except Exception as e:
            print(f"Erreur Reset : {e}")

    # --- COLLECTE DES DONNÉES ---
    for p_id in PARKS:
        try:
            response = requests.get(f"https://api.themeparks.wiki/v1/entity/{p_id}/live", timeout=15)
            data = response.json()
            
            for ride in data.get('liveData', []):
                if ride.get('entityType') == "ATTRACTION":
                    name = ride['name']
                    # On considère ouvert si OPERATING
                    is_open = (ride.get('status') == "OPERATING")
                    
                    queue = ride.get('queue', {})
                    standby = queue.get('STANDBY', {}) if queue else {}
                    wait = standby.get('waitTime', 0) if standby else 0

                    # --- LOGIQUE DE DÉCISION D'ÉCRITURE ---
                    last_record = supabase.table("disney_logs")\
                        .select("wait_time, is_open, created_at")\
                        .eq("ride_name", name)\
                        .order("created_at", desc=True)\
                        .limit(1)\
                        .execute()
                    
                    should_write = True
                    
                    if last_record.data:
                        last_wait = last_record.data[0]['wait_time']
                        last_open = last_record.data[0]['is_open']
                        
                        # A. SI L'ÉTAT CHANGE (Ouvert <-> Fermé) -> ON ÉCRIT
                        if last_open != is_open:
                            should_write = True
                        
                        # B. SI OUVERT ET TEMPS CHANGE -> ON ÉCRIT
                        elif is_open and last_wait != wait:
                            should_write = True
                            
                        # C. SI FERMÉ (PANNE) -> ON ÉCRIT TOUJOURS
                        # C'est cette condition qui empêche l'addition des pannes
                        elif not is_open:
                            should_write = True
                        
                        # D. SINON (Ouvert et même attente) -> ON N'ÉCRIT PAS
                        else:
                            should_write = False

                    if should_write:
                        # On ne supprime l'ancien record "ouvert" que si le nouvel état est AUSSI ouvert
                        # (On veut garder les traces de pannes !)
                        if is_open:
                            supabase.table("disney_logs").delete().eq("ride_name", name).eq("is_open", True).execute()
                        
                        # Insertion de l'état actuel
                        supabase.table("disney_logs").insert({
                            "ride_name": name,
                            "wait_time": wait,
                            "is_open": is_open,
                            "created_at": datetime.utcnow().isoformat()
                        }).execute()
                        
            print(f"✅ Synchro terminée pour {p_id}")
        except Exception as e:
            print(f"❌ Erreur : {e}")

if __name__ == "__main__":
    run_worker()
