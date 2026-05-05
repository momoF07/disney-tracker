import os
from supabase import create_client

URL = os.environ.get("SUPABASE_URL")
KEY = os.environ.get("SUPABASE_KEY")
supabase = create_client(URL, KEY)

def hard_reset():
    print("🔄 Hard reset en cours...")

    # 1. daily_status → remet has_opened_today à False
    supabase.table("daily_status").update({"has_opened_today": False}).neq("ride_name", "").execute()
    print("✅ daily_status réinitialisé")

    # 2. logs_101 → supprime tous les logs du jour
    supabase.table("logs_101").delete().neq("id", 0).execute()
    print("✅ logs_101 vidé")

    # 3. disney_live → remet tout le monde à fermé / 0 min
    supabase.table("disney_live").update({"is_open": False, "wait_time": 0}).neq("ride_name", "").execute()
    print("✅ disney_live réinitialisé")

    # 4. ride_schedules → vide les horaires
    supabase.table("ride_schedules").delete().neq("ride_name", "").execute()
    print("✅ ride_schedules vidé")

    print("🏁 Hard reset terminé.")

if __name__ == "__main__":
    hard_reset()