
import os
import streamlit as st

from supabase import create_client
from fpdf import FPDF

def create_account(email, password):
    try:
        response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        return response
    except Exception as e:
        return None

# 1. Load the variables from your .env file

# Hardcoding these values to bypass st.secrets discovery
SUPABASE_URL = "https://xaqttbolcbhfrsrvoghi.supabase.co"
SUPABASE_KEY = "sb_publishable_wMn2pnZiekIMxFTkv7Npw_kGvHU74R"

# Initialize directly
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
def get_user_role(user_id):
    return "tenant"

def login_user(email, password):
    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        return response
    except Exception as e:
        return None


def generate_receipt_pdf(tenant_name, amount, date):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Header
    pdf.cell(200, 10, txt="RentEasy Pro Receipt", ln=True, align='C')
    pdf.ln(10)  # Line break

    # Body
    pdf.cell(200, 10, txt=f"Tenant: {tenant_name}", ln=True)
    pdf.cell(200, 10, txt=f"Amount Paid: ${amount}", ln=True)
    pdf.cell(200, 10, txt=f"Date: {date}", ln=True)

    # Save to a temporary file
    file_path = "receipt.pdf"
    pdf.output(file_path)
    return file_path
def upload_property_image(image_file, property_id):
    # This sends the file to the 'property-images' bucket
    # We use the property_id to organize images into folders
    path_on_supa = f"{property_id}/{image_file.name}"
    try:
        response = supabase.storage.from_("property-images").upload(
            path=path_on_supa,
            file=image_file.getvalue(),
            file_options={"content-type": "image/jpeg"}
        )
        public_url = supabase.storage.from_("property-images").get_public_url(path_on_supa)
        return public_url

    except Exception as e:
        return None
