
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




def generate_lease_pdf(landlord_name, landlord_phone, tenant_name,
                           tenant_phone, property_name, property_address,
                           monthly_rent, deposit_amount, start_date, end_date):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font(family="Arial", size=12)

        # Header
        pdf.set_font(family="Arial", style="B", size=18)
        pdf.cell(w=200, h=15, txt="TENANCY AGREEMENT", ln=True, align='C')
        pdf.set_font(family="Arial", style="I", size=10)
        pdf.cell(w=200, h=10, txt="RentEasy Pro - Property Management System", ln=True, align='C')
        pdf.ln(5)

        # Divider
        pdf.set_font(family="Arial", size=12)
        pdf.cell(w=200, h=5, txt="=" * 60, ln=True)
        pdf.ln(5)

        # Parties
        pdf.set_font(family="Arial", style="B", size=13)
        pdf.cell(w=200, h=10, txt="PARTIES INVOLVED", ln=True)
        pdf.set_font(family="Arial", size=11)
        pdf.cell(w=200, h=8, txt=f"Landlord Name: {landlord_name}", ln=True)
        pdf.cell(w=200, h=8, txt=f"Landlord Phone: {landlord_phone}", ln=True)
        pdf.cell(w=200, h=8, txt=f"Tenant Name: {tenant_name}", ln=True)
        pdf.cell(w=200, h=8, txt=f"Tenant Phone: {tenant_phone}", ln=True)
        pdf.ln(5)

        # Property Details
        pdf.set_font(family="Arial", style="B", size=13)
        pdf.cell(w=200, h=10, txt="PROPERTY DETAILS", ln=True)
        pdf.set_font(family="Arial", size=11)
        pdf.cell(w=200, h=8, txt=f"Property Name: {property_name}", ln=True)
        pdf.cell(w=200, h=8, txt=f"Property Address: {property_address}", ln=True)
        pdf.ln(5)

        # Financial Terms
        pdf.set_font(family="Arial", style="B", size=13)
        pdf.cell(w=200, h=10, txt="FINANCIAL TERMS", ln=True)
        pdf.set_font(family="Arial", size=11)
        pdf.cell(w=200, h=8, txt=f"Monthly Rent: KES {monthly_rent:,.0f}", ln=True)
        pdf.cell(w=200, h=8, txt=f"Security Deposit: KES {deposit_amount:,.0f}", ln=True)
        pdf.cell(w=200, h=8, txt=f"Lease Start Date: {start_date}", ln=True)
        pdf.cell(w=200, h=8, txt=f"Lease End Date: {end_date}", ln=True)
        pdf.ln(5)

        # Terms and Conditions
        pdf.set_font(family="Arial", style="B", size=13)
        pdf.cell(w=200, h=10, txt="TERMS AND CONDITIONS", ln=True)
        pdf.set_font(family="Arial", size=10)
        terms = [
            "1. Rent is due on the 1st of every month.",
            "2. Payment shall be made via M-Pesa or agreed method.",
            "3. Tenant must maintain the property in good condition.",
            "4. Tenant must not sublet without landlord written consent.",
            "5. One month notice required before vacating.",
            "6. Deposit is refundable subject to property inspection.",
            "7. Tenant is responsible for utility bills unless agreed otherwise.",
            "8. No illegal activities permitted on the premises.",
            "9. Landlord must give 24hr notice before entering property.",
            "10. This agreement is governed by Kenyan law."
        ]
        for term in terms:
            pdf.cell(w=200, h=7, txt=term, ln=True)
        pdf.ln(5)

        # Signatures
        pdf.cell(w=200, h=5, txt="=" * 60, ln=True)
        pdf.ln(5)
        pdf.set_font(family="Arial", style="B", size=11)
        pdf.cell(w=95, h=8, txt="Landlord Signature: ____________")
        pdf.cell(w=95, h=8, txt="Tenant Signature: ____________", ln=True)
        pdf.ln(5)
        pdf.set_font(family="Arial", size=10)
        pdf.cell(w=95, h=8, txt=f"Name: {landlord_name}")
        pdf.cell(w=95, h=8, txt=f"Name: {tenant_name}", ln=True)
        pdf.cell(w=95, h=8, txt="Date: ____________")
        pdf.cell(w=95, h=8, txt="Date: ____________", ln=True)
        pdf.ln(10)

        # Footer
        pdf.set_font(family="Arial", style="I", size=9)
        pdf.cell(w=200, h=8, txt="Generated by RentEasy Pro | Kenya Property Management System",
                 ln=True, align='C')

        file_path = "lease_agreement.pdf"
        pdf.output(file_path)
        return file_path


