import os
from dotenv import load_dotenv

load_dotenv()

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Retell AI Configuration
RETELL_API_KEY = os.getenv("RETELL_API_KEY")
RETELL_WEBHOOK_SECRET = os.getenv("RETELL_WEBHOOK_SECRET")
RETELL_FROM_NUMBER = os.getenv("RETELL_FROM_NUMBER", "+1234567890")  # Default fallback number

# Server Configuration
SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("SERVER_PORT", 8000))