

from supabase import create_client
import streamlit as st

supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def record_payment(phone, amount):
    """Inserts a payment record into the database."""
    supabase.table("payments").insert({
        "phone_number": str(phone),
        "amount": float(amount),
        "status": "pending"
    }).execute()

def get_user_role(user_id):
    """Fetches user role from profiles table."""
    response = supabase.table("profiles").select("role").eq("id", user_id).single().execute()
    return response.data['role'] if response.data else None
