import requests
import os
import sys
from supabase import create_client
from datetime import datetime

# --- CONFIGURATION ---
URL = os.environ.get("SUPABASE_URL")
KEY = os.environ.get("SUPABASE_KEY")

if not URL or not KEY:
    print("❌ ERREUR : SUPABASE_URL ou KEY manquante dans l'environnement.")
    sys.exit(1)

supabase = create_client(URL, KEY)

def update_schedules():
    print("🚀 Démarrage du script de mise à jour...")
    
    # Définition de la variable park_ids à l'INTÉRIEUR de la fonction
    park_ids = [
        "dae968d5-630d-4719-8b06-3d107e944401", # Disneyland Park
        "ca888437-ebb4-4d50-aed2-d227f7096968"  # Disney Adventure World
    ]
    
    all_updates = []
    # On récupère la date du jour au format ISO YYYY-MM-DD
    current_day = datetime.now().strftime('%Y-%m-%d')
    print(f"📅 Recherche des horaires pour le : {current_day}")

    for pid in park_ids:
        api_url = f"https://api.themeparks.wiki/v1/entity/{pid}/schedule"
        print(f"🔍 Scan de l'entité : {pid}")
        sys.stdout.flush() 
        
        try:
            response = requests.get(api_url, timeout=20)
            response.raise_for_status()
            data = response.json()
            
            schedules = data.get('schedules', [])
            print(f"📊 {len(schedules)} créneaux trouvés dans l'API.")

            for entry in schedules:
                # Filtrage strict sur la date du jour
                if not entry.get('openingTime', '').startswith(current_day):
                    continue
                
                raw_type = str(entry.get('type')).upper()
                
                # Détermination du type pour Supabase
                if raw_type == 'OPERATING':
                    final_type = "PARK"
                elif raw_type in ['PERFORMANCE', 'SHOW', 'EVENT']:
                    final_type = "SHOW"
                else:
                    continue

                try:
                    # Extraction HH:MM depuis le format ISO
                    o_time = entry['openingTime'].split('T')[1][:5]
                    c_time = entry['closingTime'].split('T')[1][:5]
                    
                    all_updates.append({
                        "ride_name": entry.get('description', 'Sans nom'),
                        "opening_time": o_time,
                        "closing_time": c_time,
                        "type": final_type,
                        "updated_at": datetime.now().isoformat()
                    })
                    print(f"✅ Trouvé : {entry.get('description')} ({final_type})")
                except Exception as e:
                    print(f"⚠️ Erreur parsing ligne : {e}")
                    
        except Exception as e:
            print(f"❌ Erreur réseau/API sur {pid} : {e}")

    # --- UPSERT SUPABASE ---
    if all_updates:
        print(f"📦 Envoi de {len(all_updates)} lignes vers Supabase...")
        try:
            # L'upsert met à jour si ride_name existe déjà, sinon insère
            supabase.table("ride_schedules").upsert(all_updates).execute()
            print("✅ Mise à jour réussie !")
        except Exception as e:
            print(f"❌ Erreur Supabase : {e}")
    else:
        print("⚠️ Aucune donnée pertinente trouvée pour aujourd'hui.")

if __name__ == "__main__":
    update_schedules()