import json
from datetime import datetime

def parse_kronos_schedule(json_str):
    data = json.loads(json_str)
    extracted_shifts = []
    
    # On traite les transferShifts
    for shift in data.get('transferShifts', []):
        start_dt = shift['startDateTime']
        end_dt = shift['endDateTime']
        
        # Extraction du lieu propre
        location = "Disney"
        for segment in shift.get('segments', []):
            if segment.get('type') == "REGULAR_SEGMENT":
                qualifier = segment.get('orgJobRef', {}).get('qualifier', '')
                # On garde juste la fin après le dernier slash (ex: Accueil)
                parts = qualifier.split('/')
                if len(parts) > 1:
                    # On essaie de choper le nom de l'attraction (BTM) + la position (Accueil)
                    location = f"{parts[-2]} {parts[-1]}"
                break

        extracted_shifts.append({
            "date": start_dt.split('T')[0],
            "start_time": start_dt,
            "end_time": end_dt,
            "location": location.replace('DLP ', ''),
            "job_type": "Shift"
        })
    
    # On ajoute aussi les PayCodeEdits (Congés, Maladie, Repos payé)
    for pc in data.get('payCodeEdits', []):
        label = pc.get('payCodeRef', {}).get('qualifier', 'Repos')
        extracted_shifts.append({
            "date": pc['startDate'],
            "start_time": f"{pc['startDate']}T00:00:00",
            "end_time": f"{pc['endDate']}T23:59:59",
            "location": label,
            "job_type": "PayCode"
        })
        
    return extracted_shifts
