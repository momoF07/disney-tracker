import os
import sys
from supabase import create_client
from datetime import datetime, timedelta, timezone

# Config
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

def simulate_worker_for_ride(name, is_open, wait_time, minutes_ago=0):
    """
    Simule le worker avec la possibilité de dater l'action dans le passé.
    minutes_ago: 0 pour maintenant, 30 pour il y a 30 minutes.
    """
    # Calcul de l'heure fictive (UTC pour Supabase)
    delta = timedelta(minutes=int(minutes_ago))
    fake_now = (datetime.now(timezone.utc) - delta).isoformat()
    
    try:
        # 1. MISE À JOUR DE LA TABLE LIVE
        supabase.table("disney_live").upsert({
            "ride_name": name,
            "wait_time": int(wait_time),
            "is_open": is_open,
            "updated_at": fake_now  # On force l'heure passée
        }).execute()
        print(f"📡 Live mis à jour : {name} (T-{minutes_ago} min)")

        # 2. GESTION DU DAILY STATUS
        if is_open:
            supabase.table("daily_status").upsert({
                "ride_name": name, 
                "has_opened_today": True
            }).execute()

        # 3. GESTION DES PANNES (logs_101)
        status_check = supabase.table("daily_status").select("has_opened_today").eq("ride_name", name).execute()
        has_opened = status_check.data[0]['has_opened_today'] if status_check.data else False

        if has_opened:
            active_panne = supabase.table("logs_101").select("*").eq("ride_name", name).is_("end_time", "null").execute()
            
            if not is_open and not active_panne.data:
                # Création d'une nouvelle panne datée dans le passé
                supabase.table("logs_101").insert({
                    "ride_name": name, 
                    "start_time": fake_now # La panne commence il y a X minutes
                }).execute()
                print(f"🚨 Panne 101 créée pour {name} avec début à T-{minutes_ago} min")
            
            elif is_open and active_panne.data:
                # Fermeture de la panne à l'heure actuelle (ou fake_now si tu veux aussi décaler la fin)
                supabase.table("logs_101").update({
                    "end_time": fake_now
                }).eq("id", active_panne.data[0]['id']).execute()
                print(f"✅ Panne 101 terminée pour {name} à T-{minutes_ago} min")

    except Exception as e:
        print(f"❌ Erreur : {e}")

if __name__ == "__main__":
    # Arguments : nom, statut (open/closed), temps, minutes_ago
    if len(sys.argv) > 4:
        r_name = sys.argv[1]
        r_status = sys.argv[2] == "open"
        r_wait = sys.argv[3]
        r_ago = sys.argv[4]
        simulate_worker_for_ride(r_name, r_status, r_wait, r_ago)
    else:
        # Test manuel : simuler une panne qui a commencé il y a 45 min
        simulate_worker_for_ride("Big Thunder Mountain", is_open=False, wait_time=0, minutes_ago=45)
