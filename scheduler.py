import requests
import os
from supabase import create_client
from datetime import datetime

# --- CONFIGURATION ---
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

def update_schedules():
    # ... (init supabase)
    all_updates = []
    
    for pid in park_ids:
        api_url = f"https://api.themeparks.wiki/v1/entity/{pid}/schedule"
        res = requests.get(api_url)
        data = res.json()
        
        for entry in data.get('schedules', []):
            # On prend tout ce qui est OPERATING ou SHOW peu importe la date pour le test
            s_type = str(entry.get('type')).upper()
            if s_type in ['OPERATING', 'PERFORMANCE', 'SHOW']:
                o_time = entry['openingTime'].split('T')[1][:5]
                c_time = entry['closingTime'].split('T')[1][:5]
                
                all_updates.append({
                    "ride_name": entry.get('description'),
                    "opening_time": o_time,
                    "closing_time": c_time,
                    "type": "PARK" if s_type == 'OPERATING' else "SHOW",
                    "updated_at": "now()"
                })

    if all_updates:
        print(f"📦 Tentative d'envoi de {len(all_updates)} lignes...")
        # Utilisation de .upsert() avec on_conflict pour être sûr
        try:
            supabase.table("ride_schedules").upsert(all_updates, on_conflict="ride_name").execute()
            print("🚀 TERMINÉ : Données envoyées.")
        except Exception as e:
            print(f"❌ Erreur DB : {e}")

if __name__ == "__main__":
    update_schedules()