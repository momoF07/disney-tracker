import requests
import os
from supabase import create_client
from datetime import datetime, timezone

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
    current_day = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    print(f"📆 [SCHEDULER] Jour cible (UTC) : {current_day}")

    for pid, p_name in park_ids.items():

        # --- A. RÉCUPÉRATION DES HORAIRES (/schedule) ---
        print(f"📅 [PARK] Récupération des horaires pour {p_name}...")
        try:
            res_sched = requests.get(
                f"https://api.themeparks.wiki/v1/entity/{pid}/schedule",
                timeout=20
            )
            schedules = res_sched.json().get('schedule', [])
            print(f"   → {len(schedules)} entrée(s) reçue(s) depuis l'API")

            for entry in schedules:
                if entry.get('date') == current_day:
                    raw_type = str(entry.get('type')).upper()
                    o_time = entry['openingTime'].split('T')[1][:5]
                    c_time = entry['closingTime'].split('T')[1][:5]

                    if raw_type == 'OPERATING':
                        row = {
                            "ride_name": p_name,
                            "opening_time": o_time,
                            "closing_time": c_time,
                            "type": "PARK",
                            "updated_at": datetime.now(timezone.utc).isoformat()
                        }
                        all_updates.append(row)
                        print(f"   ✅ PARK     | {p_name} | {o_time} → {c_time}")

                    elif raw_type == 'EXTRA_HOURS':
                        row = {
                            "ride_name": f"EMT {p_name}",
                            "opening_time": o_time,
                            "closing_time": c_time,
                            "type": "EMT",
                            "updated_at": datetime.now(timezone.utc).isoformat()
                        }
                        all_updates.append(row)
                        print(f"   ✅ EMT      | EMT {p_name} | {o_time} → {c_time}")

        except Exception as e:
            print(f"❌ Erreur Park {p_name}: {e}")

        # --- B. RÉCUPÉRATION DES SHOWS (/live) ---
        print(f"🎭 [SHOWS] Extraction des spectacles pour {p_name}...")
        try:
            res_live = requests.get(
                f"https://api.themeparks.wiki/v1/entity/{pid}/live",
                timeout=20
            )
            live_data = res_live.json().get('liveData', [])
            shows = [i for i in live_data if i.get('entityType') == "SHOW"]
            print(f"   → {len(shows)} show(s) trouvé(s)")

            for item in shows:
                showtimes = item.get('showtimes', [])
                for stime in showtimes:
                    if stime.get('startTime', '').startswith(current_day):
                        start = stime['startTime'].split('T')[1][:5]
                        unique_name = f"[{p_name}] {item.get('name')} ({start})"

                        row = {
                            "ride_name": unique_name,
                            "opening_time": start,
                            "closing_time": start,
                            "type": "SHOW",
                            "updated_at": datetime.now(timezone.utc).isoformat()
                        }
                        all_updates.append(row)
                        print(f"   ✅ SHOW     | {unique_name}")

        except Exception as e:
            print(f"❌ Erreur Shows {p_name}: {e}")

    # --- RÉSUMÉ AVANT UPSERT ---
    parks = [r for r in all_updates if r["type"] == "PARK"]
    emts  = [r for r in all_updates if r["type"] == "EMT"]
    shows = [r for r in all_updates if r["type"] == "SHOW"]
    print(f"\n📊 [RÉSUMÉ] PARK: {len(parks)} | EMT: {len(emts)} | SHOWS: {len(shows)}")

    if not all_updates:
        print("⚠️ [SCHEDULER] Aucune donnée trouvée, arrêt.")
        return

    # --- DÉDOUBLONNAGE ---
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

    # --- UPSERT FINAL ---
    try:
        supabase.table("ride_schedules").upsert(
            deduped,
            on_conflict="ride_name"
        ).execute()
        print(f"✅ [SCHEDULER] Synchro terminée : {len(deduped)} lignes insérées/mises à jour.")
    except Exception as e:
        print(f"❌ Erreur Supabase : {e}")
        raise

if __name__ == "__main__":
    update_daily_schedules()