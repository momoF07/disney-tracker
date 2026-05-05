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
    print("🚀 [SCHEDULER] Démarrage de la synchro journalière...")
    
    park_ids = {
        "dae968d5-630d-4719-8b06-3d107e944401": "Disneyland Park",
        "ca888437-ebb4-4d50-aed2-d227f7096968": "Adventure World"
    }
    
    all_updates = []
    current_day = datetime.now().strftime('%Y-%m-%d')

    for pid, p_name in park_ids.items():
        # --- A. RÉCUPÉRATION DES PARCS (/schedule) ---
        print(f"📅 [PARK] Récupération des horaires pour {p_name}...")
        try:
            res_sched = requests.get(f"https://api.themeparks.wiki/v1/entity/{pid}/schedule", timeout=20)
            for entry in res_sched.json().get('schedules', []):
                if entry.get('date') == current_day:
                    raw_type = str(entry.get('type')).upper()
                    o_time = entry['openingTime'].split('T')[1][:5]
                    c_time = entry['closingTime'].split('T')[1][:5]

                    if raw_type == 'OPERATING':
                        all_updates.append({
                            "ride_name": p_name,
                            "opening_time": o_time, "closing_time": c_time,
                            "type": "PARK", "updated_at": datetime.now().isoformat()
                        })
                    elif raw_type == 'EXTRA_MAGIC_HOURS':
                        all_updates.append({
                            "ride_name": f"EMT {p_name}",
                            "opening_time": o_time, "closing_time": c_time,
                            "type": "EMT", "updated_at": datetime.now().isoformat()
                        })
        except Exception as e:
            print(f"❌ Erreur Park {p_name}: {e}")

        # --- B. RÉCUPÉRATION DES SHOWS (/live) ---
        print(f"🎭 [SHOWS] Extraction des spectacles pour {p_name}...")
        try:
            res_live = requests.get(f"https://api.themeparks.wiki/v1/entity/{pid}/live", timeout=20)
            for item in res_live.json().get('liveData', []):
                if item.get('entityType') == "SHOW":
                    showtimes = item.get('showtimes', [])
                    for stime in showtimes:
                        if stime.get('startTime', '').startswith(current_day):
                            start = stime['startTime'].split('T')[1][:5]

                            # Clé unique : parc + nom + heure → élimine les doublons inter-parcs
                            unique_name = f"[{p_name}] {item.get('name')} ({start})"

                            all_updates.append({
                                "ride_name": unique_name,
                                "opening_time": start, "closing_time": start,
                                "type": "SHOW", "updated_at": datetime.now().isoformat()
                            })
        except Exception as e:
            print(f"❌ Erreur Shows {p_name}: {e}")

    # --- UPSERT FINAL ---
    if all_updates:
        # Dédoublonnage par ride_name avant l'upsert (protection contre doublons API)
        seen = set()
        deduped = []
        for row in all_updates:
            key = row["ride_name"]
            if key not in seen:
                seen.add(key)
                deduped.append(row)

        duplicates = len(all_updates) - len(deduped)
        if duplicates:
            print(f"⚠️ [SCHEDULER] {duplicates} doublon(s) ignoré(s).")

        try:
            supabase.table("ride_schedules").upsert(deduped).execute()
            print(f"✅ [SCHEDULER] Synchro terminée : {len(deduped)} lignes insérées.")
        except Exception as e:
            print(f"❌ Erreur Supabase : {e}")
    else:
        print("⚠️ [SCHEDULER] Aucune donnée trouvée.")

if __name__ == "__main__":
    update_daily_schedules()