import pandas as pd
from supabase import create_client
import streamlit as st

# Connexion (Utilise tes propres credentials)
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

def get_all_ride_names():
    # On récupère TOUS les noms de la table sans limite de date
    response = supabase.table("disney_logs").select("ride_name").execute()
    
    if response.data:
        df = pd.DataFrame(response.data)
        # On extrait les noms uniques et on les trie
        noms_uniques = sorted(df['ride_name'].unique())
        
        print(f"--- {len(noms_uniques)} ATTRACTIONS TROUVÉES ---")
        for name in noms_uniques:
            print(f'"{name}": "🎡",') # Format prêt pour emojis.py
        
        return noms_uniques
    else:
        print("Aucune donnée trouvée dans la table.")
        return []

if __name__ == "__main__":
    get_all_ride_names()
