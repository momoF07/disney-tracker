import requests
import st # On utilise pas st.secrets ici car c'est un script brut, on passera par os.environ
import os
from supabase import create_client

# On récupère les clés depuis les variables d'environnement (configurées dans GitHub Actions)
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

# ID de Disneyland Paris sur l'API
API_URL = "https://api.themeparks.wiki/v1/entity/94f38018-8884-45e4-83f1-c06806b9044e/schedule"

def update_schedules():
    print("⏳ Récupération des horaires officiels...")
    try:
        response = requests.get(API_URL)
        data = response.json()
        
        # On prépare les données pour un "Upsert" groupé
        updates = []
        for entry in data.get('schedules', []):
            if entry['type'] == 'OPERATING':
                # Nettoyage du nom et des heures
                name = entry.get('description')
                o_time = entry['openingTime'].split('T')[1][:8] # HH:MM:SS
                c_time = entry['closingTime'].split('T')[1][:8] # HH:MM:SS
                
                updates.append({
                    "ride_name": name,
                    "opening_time": o_time,
                    "closing_time": c_time,
                    "updated_at": "now()"
                })
        
        if updates:
            supabase.table("ride_schedules").upsert(updates).execute()
            print(f"✅ {len(updates)} horaires mis à jour dans Supabase.")
            
    except Exception as e:
        print(f"❌ Erreur Scheduler : {e}")

if __name__ == "__main__":
    update_schedules()
