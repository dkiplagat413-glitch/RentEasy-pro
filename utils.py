
import os
import streamlit as st
from supabase import create_client
from fpdf import FPDF

# Initialize Supabase with service key for storage access
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = st.secrets.get("SUPABASE_SERVICE_KEY", st.secrets["SUPABASE_KEY"])

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def create_account(email, password):
    try:
        response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        return response
    except Exception as e:
        return None


def login_user(email, password):
    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        return response
    except Exception as e:
        return None


def get_user_role(user_id):
    return "tenant"


def generate_receipt_pdf(tenant_name, amount, date):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font(family="Arial", size=12)

    # Header
    pdf.set_font(family="Arial", style="B", size=16)
    pdf.cell(w=200, h=15, txt="RentEasy Pro Receipt", ln=True, align='C')
    pdf.ln(5)

    # Divider
    pdf.set_font(family="Arial", size=12)
    pdf.cell(w=200, h=5, txt="=" * 50, ln=True)
    pdf.ln(5)

    # Body
    pdf.cell(w=200, h=10, txt=f"Tenant: {tenant_name}", ln=True)
    pdf.cell(w=200, h=10, txt=f"Amount Paid: KES {amount}", ln=True)
    pdf.cell(w=200, h=10, txt=f"Date: {date}", ln=True)
    pdf.cell(w=200, h=10, txt="Status: Payment Initiated", ln=True)
    pdf.ln(5)
    pdf.cell(w=200, h=5, txt="=" * 50, ln=True)
    pdf.ln(5)
    pdf.set_font(family="Arial", style="I", size=10)
    pdf.cell(w=200, h=10, txt="Thank you for using RentEasy Pro!", ln=True, align='C')

    file_path = "receipt.pdf"
    pdf.output(file_path)
    return file_path


def upload_property_image(image_file, property_id):
    try:
        file_bytes = image_file.getvalue()
        file_name = image_file.name

        # Detect content type
        if file_name.lower().endswith(".png"):
            content_type = "image/png"
        elif file_name.lower().endswith(".jpg") or file_name.lower().endswith(".jpeg"):
            content_type = "image/jpeg"
        else:
            content_type = "image/jpeg"

        # Clean path
        path_on_supa = f"{property_id}_{file_name}".replace(" ", "_")

        # Upload using service key client
        supabase.storage.from_("property-images").upload(
            path=path_on_supa,
            file=file_bytes,
            file_options={"content-type": content_type, "upsert": "true"}
        )

        # Get public URL
        public_url = supabase.storage.from_("property-images").get_public_url(path_on_supa)
        return public_url

    except Exception as e:
        st.error(f"Image upload error: {e}")
        return None
