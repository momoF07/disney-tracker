import requests
from datetime import time, datetime

# --- CONFIGURATION PAR DÉFAUT (FALLBACK) ---
DEFAULT_DLP_CLOSE = time(22, 40)
DEFAULT_DAW_CLOSE = time(22, 40)

def get_park_schedule(api_uuid):
    """Récupère l'ouverture et la fermeture pour un UUID donné."""
    url = f"https://api.themeparks.wiki/v1/entity/{api_uuid}/schedule"
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            for entry in data.get('schedules', []):
                if entry.get('date') == today_str and entry.get('type') == 'OPERATING':
                    close_str = entry['closingTime'].split('T')[1][:5]
                    h, m = map(int, close_str.split(':'))
                    return time(h, m)
    except:
        return None
    return None

# --- RÉCUPÉRATION DYNAMIQUE ---
# ID Disneyland Park (DLP)
DLP_CLOSING = get_park_schedule("dae968d5-630d-4719-8b06-3d107e944401") or DEFAULT_DLP_CLOSE

# ID Disney Adventure World (DAW)
DAW_CLOSING = get_park_schedule("ca888437-ebb4-4d50-aed2-d227f7096968") or DEFAULT_DAW_CLOSE

# On garde ces variables pour la compatibilité avec ton app
PARK_OPENING = time(8, 30) 
PARK_CLOSING = DLP_CLOSING # Par défaut, on prend le plus tard pour l'affichage global
