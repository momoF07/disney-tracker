import json
from datetime import datetime

def parse_kronos_schedule(json_data):
    if isinstance(json_data, str):
        data = json.loads(json_data)
    else:
        data = json_data
        
    extracted_shifts = []
    
    # On parcourt les transferShifts (tes journées de travail)
    for shift in data.get('transferShifts', []):
        day_info = {
            "date": shift['startDateTime'].split('T')[0],
            "start_time": shift['startDateTime'],
            "end_time": shift['endDateTime'],
            "location": "Inconnu",
            "job_type": "Work",
            "raw_label": shift.get('label', '')
        }
        
        # On cherche le segment principal pour avoir le lieu exact (OrgJob)
        # On ignore souvent le premier segment si c'est du "trajet"
        for segment in shift.get('segments', []):
            if segment.get('type') == "REGULAR_SEGMENT":
                job_qualifier = segment.get('orgJobRef', {}).get('qualifier', '')
                # On nettoie le nom du lieu (ex: DLP BTM/404202/Accueil -> BTM Accueil)
                day_info['location'] = job_qualifier.replace('DLP ', '').replace('./DRP/DRP ThemeParks/DLP/DLP ParkOps/DLP ParkOps Attrctn/', '')
                break
        
        extracted_shifts.append(day_info)
    
    return extracted_shifts
