import os
import sys
from supabase import create_client
from datetime import datetime, timedelta
import pytz

# Config
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

def simulate_worker_for_ride(name, is_open, wait_time):
    """
    Simule le comportement complet du worker pour une attraction donnée
    selon la nouvelle architecture (Live, Status, 101).
    """
    now_utc = datetime.now(pytz.utc).isoformat()
    
    try:
        # 1. MISE À JOUR DE LA TABLE LIVE (L'instant T)
        # On utilise upsert pour écraser la ligne unique de l'attraction
        supabase.table("disney_live").upsert({
            "ride_name": name,
            "wait_time": int(wait_time),
            "is_open": is_open,
            "updated_at": now_utc
        }).execute()
        print(f"📡 Live mis à jour : {name} -> {'Ouvert' if is_open else 'Fermé'} ({wait_time} min)")

        # 2. GESTION DU DAILY STATUS (Ouverture du jour)
        if is_open:
            supabase.table("daily_status").upsert({
                "ride_name": name, 
                "has_opened_today": True
            }).execute()

        # 3. GESTION DES PANNES (logs_101)
        # On vérifie d'abord si l'attraction a déjà ouvert aujourd'hui
        status_check = supabase.table("daily_status").select("has_opened_today").eq("ride_name", name).execute()
        has_opened = status_check.data[0]['has_opened_today'] if status_check.data else False

        if has_opened:
            # On cherche une panne active (end_time est NULL)
            active_panne = supabase.table("logs_101").select("*").eq("ride_name", name).is_("end_time", "null").execute()
            
            if not is_open and not active_panne.data:
                # Création d'une nouvelle panne
                supabase.table("logs_101").insert({
                    "ride_name": name, 
                    "start_time": now_utc
                }).execute()
                print(f"🚨 Nouvelle panne 101 créée pour {name}")
            
            elif is_open and active_panne.data:
                # Fermeture de la panne en cours
                supabase.table("logs_101").update({
                    "end_time": now_utc
                }).eq("id", active_panne.data[0]['id']).execute()
                print(f"✅ Panne 101 terminée pour {name}")

    except Exception as e:
        print(f"❌ Erreur lors de la simulation : {e}")

if __name__ == "__main__":
    # Utilisation via ligne de commande
    # Arguments : nom, statut (open/closed), temps
    if len(sys.argv) > 3:
        r_name = sys.argv[1]
        r_status = sys.argv[2] == "open"
        r_wait = sys.argv[3]
        simulate_worker_for_ride(r_name, r_status, r_wait)
    else:
        # TESTS MANUELS RAPIDES :
        # Test 1 : Simuler une ouverture normale
        # simulate_worker_for_ride("Test Ride", is_open=True, wait_time=25)
        
        # Test 2 : Simuler une tombée en panne
        simulate_worker_for_ride("Test Ride", is_open=False, wait_time=0)
        
        # Test 3 : Simuler une réouverture après panne
        # simulate_worker_for_ride("Test Ride", is_open=True, wait_time=15)
