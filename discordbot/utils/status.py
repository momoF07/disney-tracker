# discordbot/utils/status.py
from datetime import datetime
import pytz

paris_tz = pytz.timezone("Europe/Paris")

STATUS_MAP = {
    "OUVERT":   {"emoji": "🟢", "label": "Opérationnel",      "color": 0x10b981},
    "INCIDENT": {"emoji": "🟠", "label": "Incident",           "color": 0xf59e0b},
    "RETARDÉ":  {"emoji": "🟣", "label": "Ouverture retardée", "color": 0xa78bfa},
    "TRAVAUX":  {"emoji": "⚫", "label": "Travaux",            "color": 0x64748b},
    "FERMÉ":    {"emoji": "🔴", "label": "Fermé",              "color": 0xef4444},
    "ATTENTE":  {"emoji": "🔵", "label": "En attente",         "color": 0x3b82f6},
    "INCONNU":  {"emoji": "⚪", "label": "Inconnu",            "color": 0x475569},
}

PARK_EMOJIS = {
    "Disneyland Park":        "🏰",
    "Disney Adventure World": "🎬",
}

def get_status(ride_data, status_map, all_pannes, heure_actuelle,
               anticipated_closings, dlp_closing, daw_closing,
               emt_opening, park_opening, emt_early_open,
               rides_daw, rehab_list):
    from datetime import time

    name    = ride_data["ride_name"]
    is_open = ride_data["is_open"]
    info    = status_map.get(name, {})

    today    = datetime.now(paris_tz).date()
    rehab    = rehab_list.get(name)
    in_rehab = False
    if rehab:
        debut = rehab.get("debut")
        fin   = rehab.get("fin")
        in_rehab = True if (not debut or not fin) else (debut <= today <= fin)

    rehab_flag = in_rehab or (
        not info.get("opened_yesterday", True)
        and not info.get("has_opened_today", False)
        and not is_open
    )

    is_daw = any(a.lower() in name.lower() for a in rides_daw)
    h_f    = anticipated_closings.get(name, daw_closing if is_daw else dlp_closing)
    h_o    = emt_opening if name in emt_early_open else park_opening

    panne_act = next((p for p in all_pannes if p["ride"] == name and p["statut"] == "EN_COURS"), None)

    if rehab_flag:
        return "TRAVAUX", "REHAB"
    elif heure_actuelle >= h_f:
        return "FERMÉ", f"Fermé à {h_f.strftime('%H:%M')}"
    elif heure_actuelle < h_o and not is_open:
        return "ATTENTE", "En attente"
    elif not is_open and not info.get("has_opened_today", False):
        return "RETARDÉ", "Ouverture retardée"
    elif not is_open:
        debut_str = panne_act["debut"].strftime("%H:%M") if panne_act else "?"
        return "INCIDENT", f"Panne depuis {debut_str}"
    else:
        return "OUVERT", f"{int(ride_data.get('wait_time', 0))} min"