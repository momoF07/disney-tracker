import requests
import requests as req
import os
from supabase import create_client
from datetime import datetime
import pytz

from config import PARK_OPENING, PARK_CLOSING, EMT_OPENING, DAW_CLOSING, DLP_CLOSING
from modules.special_hours import ANTICIPATED_CLOSINGS, EMT_EARLY_OPEN
from modules.emojis import RIDES_DAW

# Configuration Supabase
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

paris_tz = pytz.timezone('Europe/Paris')

PARKS = ["dae968d5-630d-4719-8b06-3d107e944401", "ca888437-ebb4-4d50-aed2-d227f7096968"]

# --- DISCORD WEBHOOKS ---
WEBHOOK_NOTIFS    = os.environ.get("DISCORD_WEBHOOK_NOTIFS")
WEBHOOK_DASHBOARD = os.environ.get("DISCORD_WEBHOOK_DASHBOARD")
MESSAGE_ID        = os.environ.get("DISCORD_MESSAGE_ID")

STATUS_COLORS = {
    "OUVERT":   0x10b981,
    "INCIDENT": 0xf59e0b,
    "RETARDÉ":  0xa78bfa,
    "TRAVAUX":  0x64748b,
    "FERMÉ":    0xef4444,
    "ATTENTE":  0x3b82f6,
}

STATUS_EMOJI = {
    "OUVERT":   "🟢",
    "INCIDENT": "🟠",
    "RETARDÉ":  "🟣",
    "TRAVAUX":  "⚫",
    "FERMÉ":    "🔴",
    "ATTENTE":  "🔵",
}

NOTIF_TRANSITIONS = {
    ("OUVERT", "INCIDENT"),
    ("OUVERT", "RETARDÉ"),
    ("INCIDENT", "OUVERT"),
    ("RETARDÉ", "OUVERT"),
    ("OUVERT", "TRAVAUX"),
}

def send_notif(ride_name, old_status, new_status, detail):
    if not WEBHOOK_NOTIFS: return
    if (old_status, new_status) not in NOTIF_TRANSITIONS: return

    embed = {
        "title":       f"{STATUS_EMOJI.get(new_status, '⚪')} {ride_name}",
        "description": (
            f"{STATUS_EMOJI.get(old_status, '⚪')} ~~{old_status}~~ "
            f"→ {STATUS_EMOJI.get(new_status, '⚪')} **{new_status}**"
        ),
        "color":  STATUS_COLORS.get(new_status, 0x475569),
        "fields": [
            {"name": "Détail", "value": detail, "inline": True},
            {"name": "Heure",  "value": datetime.now(paris_tz).strftime("%H:%M"), "inline": True}
        ],
        "footer": {"text": "Disney Wait Time Bot"}
    }
    try:
        req.post(WEBHOOK_NOTIFS, json={"embeds": [embed]})
    except Exception as e:
        print(f"⚠️ Notif Discord : {e}")


def send_dashboard(all_pannes, schedules, weather):
    if not WEBHOOK_DASHBOARD: return
    global MESSAGE_ID

    now    = datetime.now(paris_tz).strftime("%H:%M:%S")
    fields = []

    # Météo
    if weather and weather.get("success"):
        fields.append({
            "name":   f"{weather['emoji']} Météo",
            "value":  (
                f"**{weather['desc']}** — `{weather['temp']}°C` (Ressenti `{weather['feels_like']}°`)\n"
                f"💨 {weather['wind']} · 🚩 {weather['gusts']}"
            ),
            "inline": False
        })

    # Horaires
    parks_sched = [s for s in schedules if s.get("type") == "PARK"]
    if parks_sched:
        hours_txt = ""
        for p in parks_sched:
            name  = "DLP" if "Disneyland" in p["ride_name"] else "DAW"
            emoji = "🩷" if name == "DLP" else "🧡"
            hours_txt += f"{emoji} **{name}** : `{p['opening_time'][:5]}` → `{p['closing_time'][:5]}`\n"
        fields.append({"name": "🕒 Horaires", "value": hours_txt.strip(), "inline": False})

    # Incidents en cours
    incidents = [(p["ride"], p["debut"]) for p in all_pannes if p["statut"] == "EN_COURS"]
    if incidents:
        inc_txt = "\n".join([f"🟠 **{r}** — depuis {h}" for r, h in incidents])
        fields.append({"name": f"⚠️ {len(incidents)} incident(s) en cours", "value": inc_txt, "inline": False})
    else:
        fields.append({"name": "✅ État général", "value": "Aucun incident en cours", "inline": False})

    embed = {
        "title":       "🏰 Disney Live Board",
        "description": f"Dernière mise à jour : **{now}**",
        "color":       0x6d28d9,
        "fields":      fields,
        "footer":      {"text": "Mis à jour toutes les 10 minutes"}
    }

    try:
        if MESSAGE_ID:
            url = f"{WEBHOOK_DASHBOARD}/messages/{MESSAGE_ID}"
            res = req.patch(url, json={"embeds": [embed]})
            if res.status_code == 404:
                MESSAGE_ID = None

        if not MESSAGE_ID:
            res = req.post(f"{WEBHOOK_DASHBOARD}?wait=true", json={"embeds": [embed]})
            if res.status_code == 200:
                MESSAGE_ID = res.json().get("id")
                print(f"📌 Dashboard créé : ID {MESSAGE_ID} — ajoute DISCORD_MESSAGE_ID={MESSAGE_ID} dans les secrets GitHub")
    except Exception as e:
        print(f"⚠️ Dashboard Discord : {e}")


def get_theoretical_hours(ride_name):
    if ride_name in ANTICIPATED_CLOSINGS:
        closing = ANTICIPATED_CLOSINGS[ride_name]
    elif ride_name in RIDES_DAW:
        closing = DAW_CLOSING
    else:
        closing = DLP_CLOSING

    opening = EMT_OPENING if ride_name in EMT_EARLY_OPEN else PARK_OPENING
    return opening, closing


def is_ride_theoretically_open(current_time, opening, closing):
    if opening is None or closing is None:
        return False
    return opening <= current_time <= closing


def run_worker():
    print("⏳ [WORKER] Actualisation des attractions...")
    now_paris    = datetime.now(paris_tz)
    current_time = now_paris.time()

    # --- RESET QUOTIDIEN ---
    if now_paris.hour == 2 and now_paris.minute < 30:
        supabase.table("daily_status").update({"has_opened_today": False}).neq("ride_name", "").execute()

    # Statut pour détection de pannes
    status_db  = supabase.table("daily_status").select("*").execute()
    status_map = {item['ride_name']: item['has_opened_today'] for item in status_db.data}

    # Historique des états pour détecter les transitions
    prev_states = {}
    try:
        live_db = supabase.table("disney_live").select("ride_name,is_open").execute()
        prev_states = {item['ride_name']: item['is_open'] for item in live_db.data}
    except:
        pass

    all_pannes = []

    for p_id in PARKS:
        try:
            response  = requests.get(f"https://api.themeparks.wiki/v1/entity/{p_id}/live", timeout=15)
            live_data = response.json().get('liveData', [])

            for item in live_data:
                if item.get('entityType') == "ATTRACTION":
                    name    = item.get('name')
                    is_open = (item.get('status') == "OPERATING")
                    wait    = item.get('queue', {}).get('STANDBY', {}).get('waitTime', 0)

                    h_o, h_f         = get_theoretical_hours(name)
                    theoriquement_ouvert = is_ride_theoretically_open(current_time, h_o, h_f)
                    was_open         = prev_states.get(name, None)

                    # 1. Update Table Live
                    supabase.table("disney_live").upsert({
                        "ride_name":  name,
                        "wait_time":  wait,
                        "is_open":    is_open,
                        "updated_at": datetime.now().isoformat()
                    }).execute()

                    # 2. Détection Première Ouverture
                    if is_open and not status_map.get(name, False):
                        supabase.table("daily_status").upsert({"ride_name": name, "has_opened_today": True}).execute()

                    # 3. Logs Incidents (101) + Notifs Discord
                    active_panne = supabase.table("logs_101").select("*").eq("ride_name", name).is_("end_time", "null").execute().data

                    if not is_open and theoriquement_ouvert and not active_panne:
                        supabase.table("logs_101").insert({
                            "ride_name":  name,
                            "start_time": datetime.now().isoformat()
                        }).execute()
                        # Notif Discord : ouvert → incident
                        if was_open is True:
                            send_notif(name, "OUVERT", "INCIDENT", f"Fermée à {current_time.strftime('%H:%M')}")

                    elif is_open and active_panne:
                        supabase.table("logs_101").update({
                            "end_time": datetime.now().isoformat()
                        }).eq("id", active_panne[0]['id']).execute()
                        # Notif Discord : incident → ouvert
                        if was_open is False:
                            send_notif(name, "INCIDENT", "OUVERT", f"Réouverture à {current_time.strftime('%H:%M')}")

            print(f"✅ [WORKER] Parc {p_id} actualisé.")
        except Exception as e:
            print(f"❌ Erreur Worker: {e}")

    # --- DASHBOARD DISCORD ---
    try:
        debut_journee  = now_paris.replace(hour=2, minute=30, second=0, microsecond=0)
        resp_101       = supabase.table("logs_101").select("*").gte("start_time", debut_journee.isoformat()).execute()
        schedules_data = supabase.table("ride_schedules").select("*").execute().data or []

        from modules.weather import get_disney_weather
        weather = get_disney_weather()

        for row in resp_101.data:
            all_pannes.append({
                "ride":   row["ride_name"],
                "debut":  datetime.fromisoformat(row["start_time"]).astimezone(paris_tz).strftime("%H:%M"),
                "statut": "EN_COURS" if not row.get("end_time") else "TERMINEE"
            })

        send_dashboard(all_pannes, schedules_data, weather)
    except Exception as e:
        print(f"⚠️ Dashboard Discord : {e}")


if __name__ == "__main__":
    run_worker()