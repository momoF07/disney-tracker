import os
import sys
from supabase import create_client
from datetime import datetime, timedelta

# Config
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

def update_test_ride(name, is_open, wait_time, minutes_ago=0):
    """
    minutes_ago: permet de simuler un log dans le passé.
    0 = maintenant, 10 = il y a 10 minutes.
    """
    # Calcul de l'heure fictive
    fake_time = (datetime.utcnow() - timedelta(minutes=int(minutes_ago))).isoformat()
    
    data = {
        "ride_name": name,
        "wait_time": int(wait_time),
        "is_open": is_open,
        "created_at": fake_time
    }
    
    try:
        supabase.table("disney_logs").insert(data).execute()
        print(f"✅ Log injecté pour {name} ({'Ouvert' if is_open else 'Fermé'}) à T-{minutes_ago} min")
    except Exception as e:
        print(f"❌ Erreur : {e}")

if __name__ == "__main__":
    # Utilisation via ligne de commande (GitHub Actions)
    # Arguments : nom, statut, temps, minutes_ago
    if len(sys.argv) > 4:
        r_name = sys.argv[1]
        r_status = sys.argv[2] == "open"
        r_wait = sys.argv[3]
        r_ago = sys.argv[4]
        update_test_ride(r_name, r_status, r_wait, r_ago)
    else:
        # Utilisation manuelle pour tes tests rapides :
        # Exemple : Simuler une panne qui a commencé il y a 30 min
        update_test_ride("Test1", is_open=False, wait_time=0, minutes_ago=30)
        update_test_ride("Test1", is_open=False, wait_time=0, minutes_ago=15)
        update_test_ride("Test1", is_open=False, wait_time=0, minutes_ago=0)
