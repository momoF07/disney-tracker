import requests
import os
from supabase import create_client

# --- CONFIGURATION ---
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

if not url or not key:
    raise ValueError("Erreur : SUPABASE_URL ou SUPABASE_KEY non trouvées.")

supabase = create_client(url, key)

def update_schedules():
    # IDs stables pour Disneyland Paris (Parc principal et Studios)
    park_ids = [
        "7d979458-df68-4903-a262-63630f959550", # Parc Disneyland
        "62f3f13d-79ec-4990-bc47-194954497a7a"  # Walt Disney Studios (Adventure World)
    ]
    
    all_updates = []

    for pid in park_ids:
        api_url = f"https://api.themeparks.wiki/v1/entity/{pid}/schedule"
        print(f"⏳ Tentative sur l'ID : {pid}...")
        
        try:
            response = requests.get(api_url, timeout=20)
            
            if response.status_code == 404:
                print(f"⚠️ ID {pid} non trouvé (404).")
                continue
                
            response.raise_for_status()
            data = response.json()
            
            # Extraction des horaires
            for entry in data.get('schedules', []):
                # Filtrage : On ne prend que les ouvertures standards (OPERATING)
                if str(entry.get('type')).upper() == 'OPERATING':
                    name = entry.get('description')
                    
                    try:
                        # Formatage ISO : '2026-04-05T09:30:00' -> '09:30:00'
                        o_time = entry['openingTime'].split('T')[1][:8]
                        c_time = entry['closingTime'].split('T')[1][:8]
                        
                        all_updates.append({
                            "ride_name": name,
                            "opening_time": o_time,
                            "closing_time": c_time,
                            "updated_at": "now()"
                        })
                    except (IndexError, KeyError, TypeError):
                        continue
                        
        except Exception as e:
            print(f"❌ Erreur critique sur l'ID {pid} : {e}")

    # --- ENVOI VERS SUPABASE ---
    if all_updates:
        print(f"📦 Envoi de {len(all_updates)} attractions vers la base de données...")
        try:
            # L'upsert met à jour les horaires si le nom existe déjà
            supabase.table("ride_schedules").upsert(all_updates).execute()
            print("✅ Mise à jour réussie !")
        except Exception as e:
            print(f"❌ Erreur Supabase : {e}")
    else:
        print("⚠️ Aucune donnée d'horaire récupérée aujourd'hui.")

if __name__ == "__main__":
    update_schedules()
