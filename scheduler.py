import requests
import os
import sys
from supabase import create_client
from datetime import datetime

# --- CONFIGURATION ---
URL = os.environ.get("SUPABASE_URL")
KEY = os.environ.get("SUPABASE_KEY")
supabase = create_client(URL, KEY)

def update_daily_schedules():
    print("🚀 [SCHEDULER] Mise à jour des horaires parcs et shows...")
    
    park_ids = {
        "dae968d5-630d-4719-8b06-3d107e944401": "Disneyland Park",
        "ca888437-ebb4-4d50-aed2-d227f7096968": "Adventure World"
    }
    
    all_updates = []
    current_day = datetime.now().strftime('%Y-%m-%d')

    for pid, p_name in park_ids.items():
        api_url = f"https://api.themeparks.wiki/v1/entity/{pid}/schedule"
        
        try:
            response = requests.get(api_url, timeout=20)
            data = response.json().get('schedules', [])

            for entry in data:
                if entry.get('date') == current_day:
                    raw_type = str(entry.get('type')).upper()
                    o_time = entry['openingTime'].split('T')[1][:5]
                    c_time = entry['closingTime'].split('T')[1][:5]

                    # 1. Horaires du Parc
                    if raw_type == 'OPERATING':
                        all_updates.append({
                            "ride_name": p_name,
                            "opening_time": o_time,
                            "closing_time": c_time,
                            "type": "PARK",
                            "updated_at": datetime.now().isoformat()
                        })
                    
                    # 2. Extra Magic Time (EMT)
                    elif raw_type == 'EXTRA_MAGIC_HOURS':
                        all_updates.append({
                            "ride_name": f"EMT {p_name}",
                            "opening_time": o_time,
                            "closing_time": c_time,
                            "type": "EMT",
                            "updated_at": datetime.now().isoformat()
                        })

                    # 3. Spectacles programmés (SHOW)
                    elif raw_type in ['PERFORMANCE', 'SHOW']:
                        all_updates.append({
                            "ride_name": entry.get('description'),
                            "opening_time": o_time,
                            "closing_time": c_time,
                            "type": "SHOW",
                            "updated_at": datetime.now().isoformat()
                        })

        except Exception as e:
            print(f"❌ Erreur sur {p_name}: {e}")

    if all_updates:
        supabase.table("ride_schedules").upsert(all_updates).execute()
        print(f"✅ [SCHEDULER] {len(all_updates)} entrées synchronisées.")

if __name__ == "__main__":
    update_daily_schedules()