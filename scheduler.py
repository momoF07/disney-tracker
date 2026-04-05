import requests
import os
from supabase import create_client

# --- CONFIGURATION ---
# Ces variables sont récupérées via les secrets GitHub Actions (env)
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

# Vérification des variables d'environnement
if not url or not key:
    raise ValueError("Erreur : SUPABASE_URL ou SUPABASE_KEY non trouvées dans l'environnement.")

# Initialisation du client Supabase
supabase = create_client(url, key)

# ID de l'entité Disneyland Paris sur ThemeParks.wiki
API_URL = "https://api.themeparks.wiki/v1/entity/94f38018-8884-45e4-83f1-c06806b9044e/schedule"

def update_schedules():
    print("⏳ Connexion à l'API ThemeParks.wiki...")
    
    try:
        response = requests.get(API_URL, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        updates = []
        # On parcourt les entrées du calendrier
        for entry in data.get('schedules', []):
            # On ne récupère que les horaires de type 'OPERATING' (ouverture standard)
            if entry.get('type') == 'OPERATING':
                name = entry.get('description')
                
                # Formatage des heures (on passe de ISO 2026-04-05T09:30:00 à 09:30:00)
                try:
                    o_time = entry['openingTime'].split('T')[1][:8]
                    c_time = entry['closingTime'].split('T')[1][:8]
                    
                    updates.append({
                        "ride_name": name,
                        "opening_time": o_time,
                        "closing_time": c_time,
                        "updated_at": "now()"
                    })
                except (IndexError, KeyError):
                    continue

        if updates:
            print(f"📦 Préparation de l'envoi de {len(updates)} attractions...")
            # .upsert() met à jour si ride_name existe, sinon insère
            supabase.table("ride_schedules").upsert(updates).execute()
            print("✅ Mise à jour réussie dans Supabase.")
        else:
            print("⚠️ Aucun horaire d'ouverture trouvé pour aujourd'hui.")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur lors de la requête API : {e}")
    except Exception as e:
        print(f"❌ Erreur inattendue : {e}")

if __name__ == "__main__":
    update_schedules()
