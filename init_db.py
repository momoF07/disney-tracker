import os
from supabase import create_client
from config import PARKS_DATA

# --- CONFIGURATION ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def populate_rides_info():
    rides_to_insert = []
    
    print("🚀 Préparation des données d'attractions...")
    
    for park_name, lands in PARKS_DATA.items():
        for land_name, attractions in lands.items():
            for ride_name in attractions.keys():
                rides_to_insert.append({
                    "ride_name": ride_name,
                    "park": park_name,
                    "zone": land_name,
                    "is_exterior": False # Tu pourras modifier manuellement dans Supabase pour l'alerte orage
                })
    
    # Insertion par lot (Batch insert)
    try:
        # On utilise upsert pour éviter les doublons si on relance le script
        result = supabase.table("rides_info").upsert(
            rides_to_insert, 
            on_conflict="ride_name"
        ).execute()
        print(f"✅ Succès : {len(rides_to_insert)} attractions configurées dans rides_info.")
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation : {e}")

if __name__ == "__main__":
    populate_rides_info()