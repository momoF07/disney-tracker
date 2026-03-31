import os
from supabase import create_client
from datetime import datetime, timedelta

# Configuration (Assure-toi que tes variables d'env sont chargées ou remplace par les chaînes)
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

def inject_test_data(ride_name, is_open, wait_time, minutes_ago=0):
    # On calcule une date fictive (maintenant ou il y a X minutes)
    fake_time = (datetime.utcnow() - timedelta(minutes=minutes_ago)).isoformat()
    
    data = {
        "ride_name": ride_name,
        "wait_time": wait_time,
        "is_open": is_open,
        "created_at": fake_time
    }
    
    try:
        supabase.table("disney_logs").insert(data).execute()
        status = "OUVERT" if is_open else "FERMÉ/PANNE"
        print(f"✅ Injecté : {ride_name} | {status} | {wait_time}min | à T-{minutes_ago}min")
    except Exception as e:
        print(f"❌ Erreur : {e}")

# --- SCÉNARIOS DE TEST (À MODIFIER SELON TES BESOINS) ---
if __name__ == "__main__":
    # Supprimer les anciens tests pour y voir clair (Optionnel)
    # supabase.table("disney_logs").delete().gt("id", 0).execute()

    # Scénario 1 : Big Thunder Mountain est OUVERT avec 45min
    inject_test_data("Big Thunder Mountain", is_open=True, wait_time=45)

    # Scénario 2 : Phantom Manor est en PANNE (Fermé avec 0min)
    # On injecte aussi un log il y a 10 min pour simuler le début de la panne
    inject_test_data("Phantom Manor", is_open=False, wait_time=0, minutes_ago=10)
    inject_test_data("Phantom Manor", is_open=False, wait_time=0, minutes_ago=0)

    print("\n🚀 Données de test envoyées ! Actualise ton application Streamlit.")
