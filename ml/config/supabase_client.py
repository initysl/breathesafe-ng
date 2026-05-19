from supabase import Client, create_client

from config.settings import SUPABASE_KEY, SUPABASE_URL

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables are required")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
