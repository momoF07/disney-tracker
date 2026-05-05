import os
import requests
import re
import config as cfg
from supabase import create_client
from datetime import datetime, timezone, timedelta

# --- CONFIGURATION ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

PARKS = {
    "DLP": "dae968d5-630d-4719-8b06-3d107e944401",
    "DAW": "ca888437-ebb4-4d50-aed2-d227f7096968"
}

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

def clean_old_data():
    """Conserve 30 jours de données pour les statistiques mensuelles"""
    limit = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    try:
        supabase.table("ride_history").delete().lt("last_updated", limit).execute()
        print(f"🧹 Nettoyage : Données antérieures au {limit} supprimées.")
    except Exception as e:
        print(f"⚠️ Erreur nettoyage : {e}")

def send_discord_alert(ride_name, is_open, wait_time):
    if not DISCORD_WEBHOOK_URL: return
    color = 0x2ECC71 if is_open else 0xE74C3C
    status_text = "✅ RÉOUVERTURE" if is_open else "⚠️ INTERRUPTION"
    payload = {
        "embeds": [{
            "title": f"🎢 {status_text}",
            "description": f"**{ride_name}** est désormais {'ouvert' if is_open else 'en panne'}.",
            "color": color,
            "fields": [
                {"name": "Temps d'attente", "value": f"{wait_time} min", "inline": True},
                {"name": "Heure", "value": datetime.now().strftime("%H:%M"), "inline": True}
            ],
            "footer": {"text": "Disney Tracker Live Update"}
        }]
    }
    try: requests.post(DISCORD_WEBHOOK_URL, json=payload)
    except: pass

def super_clean(text):
    if not text: return ""
    return re.sub(r'[^a-z0-9]', '', text.lower())

def fetch_and_sync():
    clean_allowed_map = {super_clean(name): name for name in cfg.ALL_RIDES_LIST}
    for park_code, park_id in PARKS.items():
        url = f"https://api.themeparks.wiki/v1/entity/{park_id}/live"
        try:
            response = requests.get(url, timeout=15)
            data = response.json().get('liveData', [])
            for item in data:
                if item.get('entityType', '').upper() == 'ATTRACTION':
                    api_name_clean = super_clean(item.get('name', ''))
                    if api_name_clean in clean_allowed_map:
                        process_ride(item, clean_allowed_map[api_name_clean])
        except Exception as e: print(f"❌ Erreur {park_code}: {e}")

def process_ride(item, official_name):
    status = item.get('status', 'CLOSED')
    wait = item.get('queue', {}).get('STANDBY', {}).get('waitTime', 0)
    is_open = (status == 'OPERATING')
    now = datetime.now(timezone.utc).isoformat()

    try:
        supabase.table("disney_live").upsert({
            "ride_name": official_name, "wait_time": wait, "is_open": is_open, 
            "status": status, "last_updated": now
        }).execute()
        
        if is_open:
            supabase.table("ride_history").insert({
                "ride_name": official_name, "wait_time": wait, "last_updated": now
            }).execute()
        
        handle_breakdown_logic(official_name, status, wait)
    except Exception as e: print(f"⚠️ Erreur Supabase {official_name}: {e}")

def handle_breakdown_logic(name, current_status, current_wait):
    try:
        open_log = supabase.table("logs_101").select("*").eq("ride_name", name).is_("end_time", "null").execute()
        if current_status == "DOWN" and not open_log.data:
            supabase.table("logs_101").insert({"ride_name": name, "start_time": datetime.now().isoformat()}).execute()
            send_discord_alert(name, False, current_wait)
        elif current_status == "OPERATING" and open_log.data:
            supabase.table("logs_101").update({"end_time": datetime.now().isoformat()}).eq("id", open_log.data[0]['id']).execute()
            send_discord_alert(name, True, current_wait)
    except: pass

def fetch_shows():
    url = "https://api.themeparks.wiki/v1/entity/e8d0207f-da8a-4048-bec8-117aa946b2c2/live"
    try:
        data = requests.get(url).json().get('liveData', [])
        now = datetime.now(timezone.utc)
        for item in data:
            if item.get('entityType') == 'SHOW':
                for slot in item.get('showtimes', []):
                    start_dt = datetime.fromisoformat(slot.get('startTime'))
                    park_name = "DAW" if item.get('parkId') == "ca888437-ebb4-4d50-aed2-d227f7096968" else "DLP"
                    supabase.table("show_times").upsert({
                        "show_name": item.get('name'), "park": park_name, "start_time": slot.get('startTime'),
                        "is_performed": now > start_dt, "updated_at": now.isoformat()
                    }, on_conflict="show_name, start_time").execute()
    except: pass

def fetch_park_schedules():
    for code, pid in PARKS.items():
        try:
            res = requests.get(f"https://api.themeparks.wiki/v1/entity/{pid}/schedule").json()
            for entry in res:
                payload = {"park_id": code, "date": entry.get('date'), "updated_at": datetime.now().isoformat()}
                if entry.get('type') == "OPERATING":
                    payload.update({"opening_time": entry.get('openingTime'), "closing_time": entry.get('closingTime')})
                elif entry.get('type') == "EXTRA_MAGIC_HOURS":
                    payload.update({"emt_opening_time": entry.get('openingTime'), "emt_closing_time": entry.get('closingTime')})
                supabase.table("park_schedule").upsert(payload, on_conflict="park_id, date").execute()
        except: pass

if __name__ == "__main__":
    fetch_and_sync()
    fetch_shows()
    fetch_park_schedules()
    clean_old_data()