import os
import pandas as pd
from supabase import create_client

# Récupération des secrets depuis l'environnement GitHub
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

if not url or not key:
    print("❌ Erreur : Les secrets SUPABASE_URL ou SUPABASE_KEY sont manquants.")
    exit(1)

supabase = create_client(url, key)

def get_all_ride_names():
    print("⏳ Connexion à Supabase...")
    response = supabase.table("disney_logs").select("ride_name").execute()
    
    if response.data:
        df = pd.DataFrame(response.data)
        noms_uniques = sorted(df['ride_name'].unique())
        
        print(f"\n--- {len(noms_uniques)} ATTRACTIONS TROUVÉES ---\n")
        print("Copie-colle cette liste pour ton fichier emojis.py :\n")
        for name in noms_uniques:
            print(f'    "{name}": "🎡",')
    else:
        print("📭 Aucune donnée trouvée.")

if __name__ == "__main__":
    get_all_ride_names()
