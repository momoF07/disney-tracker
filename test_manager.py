import os
import sys
from supabase import create_client
from datetime import datetime

# Config
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

def update_test_ride(name, is_open, wait_time):
    # On nettoie si c'est ouvert pour simuler ton worker hybride
    if is_open:
        supabase.table("disney_logs").delete().eq("ride_name", name).execute()
    
    data = {
        "ride_name": name,
        "wait_time": int(wait_time),
        "is_open": is_open,
        "created_at": datetime.utcnow().isoformat()
    }
    supabase.table("disney_logs").insert(data).execute()
    print(f"✅ {name} mis à jour via GitHub Action.")

if __name__ == "__main__":
    # Récupération des arguments envoyés par le YAML
    r_name = sys.argv[1]
    r_status = sys.argv[2] == "open"
    r_wait = sys.argv[3]
    
    update_test_ride(r_name, r_status, r_wait)
