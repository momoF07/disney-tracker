# discordbot/bot/supabase_client.py
from supabase import create_client
import os

_client = None

def get_supabase():
    global _client
    if _client is None:
        _client = create_client(
            os.environ.get("SUPABASE_URL"),
            os.environ.get("SUPABASE_KEY")
        )
    return _client