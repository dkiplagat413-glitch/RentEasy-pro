
import os
import streamlit as st
from dotenv import load_dotenv
from supabase import create_client

# 1. Load the variables from your .env file
load_dotenv(dotenv_path='.env')

# 2. Get the values
url = os.environ.get("SUPABASE_URL", "").strip()
key = os.environ.get("SUPABASE_KEY", "").strip()


# 3. Debug
print(f"DEBUG: URL is '{url}'")
print(f"DEBUG: Key is '{key}'")

# 4. Initialize
supabase = create_client(url, key)

def record_payment(phone, amount):
    # ... keep your existing function here ...
    pass

def get_user_role(user_id):
    # ... keep your existing function here ...
    pass