import requests
import os
from supabase import create_client
from datetime import datetime

# --- CONFIGURATION ---
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

def update_schedules():
    # ID du complexe Disneyland Paris pour récupérer TOUS les shows et horaires d'un coup
    # Ou garder tes IDs de parcs si tu préfères filtrer par parc
    park_ids = [
        "dae968d5-630d-4719-8b06-3d107e944401", # Parc Disneyland
        "ca888437-ebb4-4d50-aed2-d227f7096968"  # Disney Adventure World
    ]
    
    all_updates = []
    current_day = datetime.now().strftime('%Y-%m-%d')

    for pid in park_ids:
        # Endpoint schedule
        api_url = f"https://api.themeparks.wiki/v1/entity/{pid}/schedule"
        
        try:
            response = requests.get(api_url, timeout=20)
            response.raise_for_status()
            data = response.json()
            
            for entry in data.get('schedules', []):
                # On ne prend que les données du jour actuel
                if not entry.get('openingTime', '').startswith(current_day):
                    continue
                
                s_type = str(entry.get('type')).upper()
                # On accepte OPERATING (Parcs) et PERFORMANCE ou SHOW (Spectacles)
                if s_type in ['OPERATING', 'PERFORMANCE', 'SHOW']:
                    try:
                        o_time = entry['openingTime'].split('T')[1][:5] # Format HH:MM
                        c_time = entry['closingTime'].split('T')[1][:5]
                        
                        all_updates.append({
                            "ride_name": entry.get('description', 'Spectacle'),
                            "opening_time": o_time,
                            "closing_time": c_time,
                            "type": "PARK" if s_type == 'OPERATING' else "SHOW",
                            "updated_at": "now()"
                        })
                    except: continue
                        
        except Exception as e:
            print(f"❌ Erreur sur l'ID {pid} : {e}")

    if all_updates:
        # Note: Assure-toi d'avoir ajouté la colonne 'type' dans ta table Supabase
        supabase.table("ride_schedules").upsert(all_updates).execute()
        print(f"✅ {len(all_updates)} horaires/shows mis à jour.")

if __name__ == "__main__":
    update_schedules()