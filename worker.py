import requests
import requests as req
import os
from supabase import create_client
from datetime import datetime, time
import pytz

from config import PARK_OPENING, PARK_CLOSING, EMT_OPENING, DAW_CLOSING, DLP_CLOSING
from modules.special_hours import ANTICIPATED_CLOSINGS, FANTASYLAND_EARLY_CLOSE, EMT_EARLY_OPEN, SPECIAL_OPENING_HOURS
from modules.emojis import RIDES_DAW, PARKS_DATA
from modules.rehabilitations import REHAB_LIST

# Configuration Supabase
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

paris_tz = pytz.timezone('Europe/Paris')

PARKS = ["dae968d5-630d-4719-8b06-3d107e944401", "ca888437-ebb4-4d50-aed2-d227f7096968"]

# --- DISCORD WEBHOOKS ---
WEBHOOK_NOTIFS = os.environ.get("DISCORD_WEBHOOK_NOTIFS")
WEBHOOK_DLP    = os.environ.get("DISCORD_WEBHOOK_DLP")
WEBHOOK_DAW    = os.environ.get("DISCORD_WEBHOOK_DAW")
MESSAGE_ID_DLP = os.environ.get("DISCORD_MESSAGE_ID_DLP")
MESSAGE_ID_DAW = os.environ.get("DISCORD_MESSAGE_ID_DAW")

STATUS_COLORS = {
    "OUVERT":    0x10b981,
    "INCIDENT":  0xf59e0b,
    "RETARDÉ":   0xa78bfa,
    "TRAVAUX":   0x64748b,
    "FERMÉ":     0x991b1b,
    "ATTENTE":   0x3b82f6,
    "FERMETURE": 0x991b1b,
    "RÉOUVERT":  0x10b981,
}

STATUS_EMOJI = {
    "OUVERT":    "🟢",
    "INCIDENT":  "🟠",
    "RETARDÉ":   "🟣",
    "TRAVAUX":   "⚫",
    "FERMÉ":     "🔴",
    "ATTENTE":   "🔵",
    "FERMETURE": "🏁",
    "RÉOUVERT":  "✅",
}

NOTIF_TRANSITIONS = {
    ("OUVERT",   "INCIDENT"),
    ("INCIDENT", "RÉOUVERT"),
    ("ATTENTE",  "RETARDÉ"),
    ("RETARDÉ",  "OUVERT"),
    ("ATTENTE",  "OUVERT"),
    ("OUVERT",   "FERMETURE"),
    ("INCIDENT", "FERMETURE"),
    ("OUVERT",   "TRAVAUX"),
}


# ============================================================
# NOTIFICATIONS DISCORD
# ============================================================
def send_notif(ride_name, old_status, new_status, detail=""):
    if not WEBHOOK_NOTIFS:
        return
    if (old_status, new_status) not in NOTIF_TRANSITIONS:
        return

    heure = datetime.now(paris_tz).strftime("%H:%M")
    e_old = STATUS_EMOJI.get(old_status, "⚪")
    e_new = STATUS_EMOJI.get(new_status, "⚪")

    embed = {
        "title":       f"{e_new} {ride_name}",
        "description": f"{e_old} ~~{old_status}~~ → {e_new} **{new_status}**",
        "color":       STATUS_COLORS.get(new_status, 0x475569),
        "fields": [
            {"name": "Détail", "value": detail or "—", "inline": True},
            {"name": "Heure",  "value": heure,          "inline": True},
        ],
        "footer": {"text": "Disney Wait Time Bot"}
    }
    try:
        req.post(WEBHOOK_NOTIFS, json={"embeds": [embed]})
        print(f"  📣 Notif → {ride_name} : {old_status} → {new_status}")
    except Exception as e:
        print(f"⚠️ Notif Discord : {e}")


# ============================================================
# CALCUL DU STATUT — même logique que app.py
# ============================================================
def compute_status(name, is_open, info, heure_act, today):
    is_daw = name in RIDES_DAW

    # Heure de fermeture
    if name in ANTICIPATED_CLOSINGS:
        h_f = ANTICIPATED_CLOSINGS[name]
    elif name in FANTASYLAND_EARLY_CLOSE:
        h_f = time(DLP_CLOSING.hour - 1, DLP_CLOSING.minute)
    else:
        h_f = DAW_CLOSING if is_daw else DLP_CLOSING

    # Heure d'ouverture
    h_o = EMT_OPENING if name in EMT_EARLY_OPEN else PARK_OPENING
    if name in SPECIAL_OPENING_HOURS:
        h_o = SPECIAL_OPENING_HOURS[name]

    # Rehab (liste statique + logique daily_status)
    rehab    = REHAB_LIST.get(name)
    in_rehab = False
    if rehab:
        debut    = rehab.get('debut')
        fin      = rehab.get('fin')
        in_rehab = (not debut or not fin) or (debut <= today <= fin)

    rehab_flag = in_rehab or (
        not info.get('opened_yesterday', True)
        and not info.get('has_opened_today', False)
        and not is_open
    )

    # Priorités identiques à app.py
    if rehab_flag:
        return "TRAVAUX", h_o, h_f
    elif heure_act >= h_f:
        return "FERMETURE", h_o, h_f
    elif heure_act < h_o and not is_open:
        return "ATTENTE", h_o, h_f
    elif not is_open and not info.get('has_opened_today', False):
        return "RETARDÉ", h_o, h_f
    elif not is_open:
        return "INCIDENT", h_o, h_f
    else:
        return "OUVERT", h_o, h_f


# ============================================================
# MÉTÉO
# ============================================================
def get_weather_simple():
    try:
        res = requests.get(
            "https://api.open-meteo.com/v1/forecast"
            "?latitude=48.8675&longitude=2.7841"
            "&current=temperature_2m,apparent_temperature,weather_code,wind_speed_10m,wind_gusts_10m"
            "&timezone=Europe%2FParis",
            timeout=5
        )
        data = res.json().get('current', {})
        weather_map = {
            0:  ("☀️",  "Ciel dégagé"),
            1:  ("🌤️", "Plutôt beau"),
            2:  ("⛅",  "Partiellement nuageux"),
            3:  ("☁️",  "Couvert"),
            45: ("🌫️", "Brouillard"),
            51: ("🌦️", "Bruine"),
            61: ("🌧️", "Pluie faible"),
            63: ("🌧️", "Pluie modérée"),
            80: ("🌦️", "Averses"),
            95: ("⛈️",  "Orage"),
        }
        code        = data.get('weather_code', -1)
        emoji, desc = weather_map.get(code, ("🌡️", "Météo stable"))
        return {
            "temp":       data.get('temperature_2m', '--'),
            "feels_like": data.get('apparent_temperature', '--'),
            "wind":       f"{round(data.get('wind_speed_10m', 0))} km/h",
            "gusts":      f"{round(data.get('wind_gusts_10m', 0))} km/h",
            "desc":       desc,
            "emoji":      emoji,
            "success":    True
        }
    except Exception as e:
        print(f"⚠️ Météo : {e}")
        return {"success": False}


# ============================================================
# DASHBOARD DISCORD
# ============================================================
def send_park_embed(park_name, lands, webhook_url, all_pannes, schedules, weather, live_map, status_map, heure_act, today):
    global MESSAGE_ID_DLP, MESSAGE_ID_DAW

    is_dlp     = "Disneyland" in park_name
    park_emoji = "🏰" if is_dlp else "🎬"
    now        = datetime.now(paris_tz).strftime("%H:%M:%S")
    fields     = []

    # Météo (DLP uniquement)
    if is_dlp and weather and weather.get("success"):
        fields.append({
            "name":   f"{weather['emoji']} Météo",
            "value":  (
                f"**{weather['desc']}** — `{weather['temp']}°C`"
                f" (Ressenti `{weather['feels_like']}°`)"
                f" · 💨 {weather['wind']} · 🚩 {weather['gusts']}"
            ),
            "inline": False
        })

    # Horaires du parc
    park_key    = "Disneyland Park" if is_dlp else "Adventure World"
    parks_sched = [s for s in schedules if s.get("type") == "PARK" and park_key in s.get("ride_name", "")]
    emts        = [s for s in schedules if s.get("type") == "EMT"  and park_key in s.get("ride_name", "")]
    if parks_sched:
        p       = parks_sched[0]
        emt_str = f" · ✨ EMT `{emts[0]['opening_time'][:5]}`" if emts else ""
        fields.append({
            "name":   "🕒 Horaires",
            "value":  f"`{p['opening_time'][:5]}` → `{p['closing_time'][:5]}`{emt_str}",
            "inline": False
        })

    # Statut par attraction
    def get_ride_display(attr_name):
        data = live_map.get(attr_name)
        # Fallback fuzzy si guillemets Unicode dans le nom
        if not data:
            clean = attr_name.lower().strip('"\u201c\u201d\u2018\u2019')
            for k, v in live_map.items():
                if k.lower().strip('"\u201c\u201d\u2018\u2019') == clean:
                    data = v
                    break
        if not data:
            return "⚪", "--"

        is_open      = data.get('is_open', False)
        wait         = data.get('wait_time', 0)
        info         = status_map.get(attr_name, {})
        status, _, _ = compute_status(attr_name, is_open, info, heure_act, today)

        emoji = STATUS_EMOJI.get(status, "⚪")
        if status == "OUVERT":
            label = f"{int(wait)} min"
        elif status == "INCIDENT":
            debut_p = next(
                (p['debut'] for p in all_pannes if p['ride'] == attr_name and p['statut'] == 'EN_COURS'),
                '?'
            )
            label = f"101 depuis {debut_p}"
        else:
            label = status
        return emoji, label

    for land, attractions in lands.items():
        lines = []
        for attr_name in attractions:
            e, d = get_ride_display(attr_name)
            lines.append(f"{e} {attr_name} — `{d}`")

        chunk = ""
        for line in lines:
            if len(chunk) + len(line) + 1 > 1020:
                fields.append({"name": land.title(), "value": chunk.strip(), "inline": False})
                chunk = line + "\n"
            else:
                chunk += line + "\n"
        if chunk.strip():
            fields.append({"name": land.title(), "value": chunk.strip(), "inline": False})

    embed = {
        "title":       f"{park_emoji} {park_name}",
        "description": f"Dernière mise à jour : **{now}**",
        "color":       0xffb3d1 if is_dlp else 0xfb923c,
        "fields":      fields[:25],
        "footer":      {"text": "Mis à jour toutes les 10 minutes"}
    }

    try:
        mid = MESSAGE_ID_DLP if is_dlp else MESSAGE_ID_DAW
        if mid:
            res = req.patch(f"{webhook_url}/messages/{mid}", json={"embeds": [embed]})
            if res.status_code == 404:
                mid = None

        if not mid:
            res = req.post(f"{webhook_url}?wait=true", json={"embeds": [embed]})
            if res.status_code == 200:
                new_id = res.json().get("id")
                if is_dlp:
                    MESSAGE_ID_DLP = new_id
                    print(f"📌 DLP Dashboard créé : ID {new_id} — ajoute DISCORD_MESSAGE_ID_DLP={new_id}")
                else:
                    MESSAGE_ID_DAW = new_id
                    print(f"📌 DAW Dashboard créé : ID {new_id} — ajoute DISCORD_MESSAGE_ID_DAW={new_id}")
    except Exception as e:
        print(f"⚠️ Dashboard {park_name} : {e}")


def send_dashboard(all_pannes, schedules, weather):
    now_paris = datetime.now(paris_tz)
    heure_act = now_paris.time()
    today     = now_paris.date()

    try:
        live_db    = supabase.table("disney_live").select("*").execute()
        status_db  = supabase.table("daily_status").select("*").execute()
        live_map   = {item['ride_name']: item for item in live_db.data}
        status_map = {item['ride_name']: item for item in status_db.data}
    except:
        live_map   = {}
        status_map = {}

    for park_name, lands in PARKS_DATA.items():
        webhook = WEBHOOK_DLP if "Disneyland" in park_name else WEBHOOK_DAW
        if not webhook:
            continue
        send_park_embed(
            park_name, lands, webhook,
            all_pannes, schedules, weather,
            live_map, status_map, heure_act, today
        )


# ============================================================
# WORKER PRINCIPAL
# ============================================================
def run_worker():
    print("⏳ [WORKER] Actualisation des attractions...")
    now_paris    = datetime.now(paris_tz)
    current_time = now_paris.time()
    today        = now_paris.date()

    # --- RESET QUOTIDIEN ---
    if now_paris.hour == 2 and 25 <= now_paris.minute <= 35:
        supabase.table("daily_status").update({"has_opened_today": False}).neq("ride_name", "").execute()
        print("🌙 Reset quotidien effectué.")

    # Chargement daily_status
    status_db  = supabase.table("daily_status").select("*").execute()
    status_map = {item['ride_name']: item for item in status_db.data}

    # ----------------------------------------------------------------
    # Lecture de disney_live pour prev_open ET last_status (FIX)
    # ----------------------------------------------------------------
    try:
        live_db       = supabase.table("disney_live").select("ride_name,is_open,last_status").execute()
        prev_open     = {item['ride_name']: item['is_open']           for item in live_db.data}
        prev_statuses = {item['ride_name']: item.get('last_status')   for item in live_db.data}
    except:
        prev_open     = {}
        prev_statuses = {}

    all_pannes = []

    for p_id in PARKS:
        try:
            response  = requests.get(f"https://api.themeparks.wiki/v1/entity/{p_id}/live", timeout=15)
            live_data = response.json().get('liveData', [])

            for item in live_data:
                if item.get('entityType') != "ATTRACTION":
                    continue

                name    = item.get('name')
                is_open = (item.get('status') == "OPERATING")
                wait    = item.get('queue', {}).get('STANDBY', {}).get('waitTime', 0)
                info    = status_map.get(name, {})

                # Calcul du nouveau statut
                new_status, h_o, h_f = compute_status(name, is_open, info, current_time, today)
                old_status            = prev_statuses.get(name)

                # --- 1. UPDATE TABLE LIVE (last_status inclus) ---
                supabase.table("disney_live").upsert({
                    "ride_name":   name,
                    "wait_time":   wait,
                    "is_open":     is_open,
                    "last_status": new_status,
                    "updated_at":  datetime.now().isoformat()
                }).execute()

                # --- 2. PREMIÈRE OUVERTURE DU JOUR ---
                if is_open and not info.get('has_opened_today', False):
                    supabase.table("daily_status").upsert({
                        "ride_name":        name,
                        "has_opened_today": True
                    }).execute()
                    status_map[name] = {**info, "has_opened_today": True}

                # --- 3. LOGS INCIDENTS (101) ---
                active_panne         = supabase.table("logs_101")\
                    .select("*")\
                    .eq("ride_name", name)\
                    .is_("end_time", "null")\
                    .execute().data
                theoriquement_ouvert = (h_o <= current_time < h_f)

                if not is_open and theoriquement_ouvert and not active_panne:
                    supabase.table("logs_101").insert({
                        "ride_name":  name,
                        "start_time": datetime.now().isoformat()
                    }).execute()

                elif is_open and active_panne:
                    supabase.table("logs_101").update({
                        "end_time": datetime.now().isoformat()
                    }).eq("id", active_panne[0]['id']).execute()

                # --- 4. NOTIFICATIONS DISCORD ---
                # Seulement si le statut a vraiment changé
                if old_status and old_status != new_status:
                    heure_str = current_time.strftime('%H:%M')

                    # Cas spécial : INCIDENT → OUVERT = Réouverture
                    notif_new = new_status
                    if old_status == "INCIDENT" and new_status == "OUVERT":
                        notif_new = "RÉOUVERT"

                    if notif_new == "INCIDENT":
                        detail = f"Interruption détectée à {heure_str}"
                    elif notif_new == "RÉOUVERT":
                        detail = f"Réouverture à {heure_str}"
                    elif notif_new == "RETARDÉ":
                        detail = f"Ouverture prévue à {h_o.strftime('%H:%M')}, pas encore ouverte"
                    elif notif_new == "OUVERT" and old_status in ("ATTENTE", "RETARDÉ"):
                        detail = f"Première ouverture à {heure_str}"
                    elif notif_new == "FERMETURE":
                        detail = f"Fermeture pour la nuit à {h_f.strftime('%H:%M')}"
                    elif notif_new == "TRAVAUX":
                        detail = "Réhabilitation détectée"
                    else:
                        detail = f"{old_status} → {notif_new}"

                    send_notif(name, old_status, notif_new, detail)

            print(f"✅ [WORKER] Parc {p_id} actualisé.")
        except Exception as e:
            print(f"❌ Erreur Worker parc {p_id} : {e}")

    # --- DASHBOARD DISCORD ---
    try:
        debut_journee  = now_paris.replace(hour=2, minute=30, second=0, microsecond=0)
        resp_101       = supabase.table("logs_101").select("*").gte("start_time", debut_journee.isoformat()).execute()
        schedules_data = supabase.table("ride_schedules").select("*").execute().data or []
        weather        = get_weather_simple()

        for row in resp_101.data:
            all_pannes.append({
                "ride":   row["ride_name"],
                "debut":  datetime.fromisoformat(row["start_time"]).astimezone(paris_tz).strftime("%H:%M"),
                "statut": "EN_COURS" if not row.get("end_time") else "TERMINEE"
            })

        send_dashboard(all_pannes, schedules_data, weather)
        print("✅ [WORKER] Dashboard Discord mis à jour.")
    except Exception as e:
        print(f"⚠️ Dashboard Discord : {e}")


if __name__ == "__main__":
    run_worker()