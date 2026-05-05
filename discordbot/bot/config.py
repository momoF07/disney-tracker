# bot/config.py
import os

DISCORD_TOKEN      = os.environ.get("DISCORD_TOKEN")
SUPABASE_URL       = os.environ.get("SUPABASE_URL")
SUPABASE_KEY       = os.environ.get("SUPABASE_KEY")

# IDs à remplir après création des channels Discord
CHANNEL_NOTIFS_ID  = int(os.environ.get("CHANNEL_NOTIFS_ID",  "0"))
CHANNEL_DASHBOARD_ID = int(os.environ.get("CHANNEL_DASHBOARD_ID", "0"))
MESSAGE_DASHBOARD_ID = int(os.environ.get("MESSAGE_DASHBOARD_ID", "0"))  # ID du message épinglé

# Intervalle de polling en secondes
POLL_INTERVAL = 60