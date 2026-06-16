

import streamlit as st
import pandas as pd
import requests
import base64
import sqlite3
import os
from supabase import create_client
from datetime import datetime
from st_login_form import login_form
from utils import supabase
from utils import generate_receipt_pdf
from utils import upload_property_image
from utils import supabase, login_user, create_account

# 1. Setup
st.set_page_config(page_title="RentEasy Pro", layout="wide")
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])


# 2. Function Definition (Defined before use)
def login_user(email, password):
    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        return response
    except Exception as e:
        return e


# 3. Main Logic (Left-aligned, clear flow)
if "user" not in st.session_state:
    st.session_state.user = None



# Sidebar selection
menu = st.sidebar.selectbox("Menu", ["Login", "Sign Up"])

# 2. Login Section
if menu == "Login":
    st.subheader("RentEasy Pro Login")
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")

    if st.button("Submit", key="login_btn"):
        # Ensure you are passing the correct arguments here
        result = login_user(email, password)
        if hasattr(result, 'user'):
            st.success("Logged in successfully!")
        else:
            st.error("Login failed. Check your credentials.")

# 3. Sign Up Section
elif menu == "Sign Up":
    st.subheader("Create New Account")
    new_email = st.text_input("Email", key="signup_email")
    new_password = st.text_input("Password", type="password", key="signup_password")
    confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")

    if st.button("Register", key="signup_btn"):
        if new_password != confirm_password:
            st.error("Passwords do not match!")
        else:
            try:
                # Use the 'supabase' client you initialized at the top
                response = supabase.auth.sign_up({"email": new_email, "password": new_password})
                st.success("Account created! Please navigate to the Login page.")
            except Exception as e:
                st.error(f"Error: {e}")

                st.stop()


    st.title("Welcome to RentEasy Pro")


    st.session_state["user"] = None

if "user" not in st.session_state:
    st.session_state["user"] = None

if st.session_state.get("user") is None:
    st.title("RentEasy Pro Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Submit"):
        # 1. Add validation: Check if fields are empty
        if not email or not password:
            st.error("Please enter both email and password.")
        else:
            # 2. Call your authentication function (e.g., login_user from utils.py)
            user = login_user(email, password)

            if user:
                st.session_state["user"] = user
                st.rerun()  # Forces the app to refresh and see the 'user' is logged in
            else:
                st.error("Login failed. Check your credentials.")

    # The stop() is still here, but now it's correctly
    # guarded by the session state logic above.
    st.stop()

# --- DASHBOARD (This area is now hidden until login succeeds) ---
st.title("Welcome to the Dashboard")

with st.sidebar:
            st.title("RentEasy Pro")
            page = st.radio("Navigation", ["Dashboard", "Properties", "Tenants", "Payments", "Reports"])
            st.divider()
            st.write("Settings")

        # Main content switch
if page == "Dashboard":
    def show_maintenance_section():
        st.subheader("🛠️ Maintenance Requests")

        # This query fetches all requests AND the linked property name
        # Ensure the foreign key relationship allows this join
        response = supabase.table("maintenance_request").select("*, properties(name)").execute()
        requests = response.data

        if requests:
            for req in requests:
                # Safely get the property name from the joined table
                prop_name = req.get('properties', {}).get('name', 'Unknown Property')

                with st.container(border=True):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**Property:** {prop_name}")
                        st.write(f"**Issue:** {req.get('description', 'No description')}")
                    with col2:
                        st.status(req.get('status', 'Pending'))
                        st.write(f"Cost: KES {req.get('cost', 0)}")
        else:
            st.info("No active maintenance requests.")

    st.header("Executive Summary")
            # ... Dashboard code
        # Create a row of metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Properties", "12", "+2")
    col2.metric("Occupied", "10", "85%")
    col3.metric("Revenue (KES)", "150,000", "+12%")
    col4.metric("Pending", "2", "High Priority")


        # Fetch properties from Supabase here
    response = supabase.table("properties").select("*").execute()
    properties = response.data

        # 2. RENDER THE GALLERY
    st.subheader("Property Portfolio")




    if properties:
            cols = st.columns(3)
            for i, prop in enumerate(properties):
                with cols[i % 3]:
                    # Use .get() with PARENTHESES ()
                    st.image(prop.get('image_url', ''), use_column_width=True)
                    st.write(f"**{prop.get('name', 'Unknown')}**")
                    st.write(f"Status: {prop.get('status', 'N/A')}")
    else:
            st.info("No properties found in database.")

            with st.container(border=True):
                    st.subheader("Quick Actions")
                    c1, c2 = st.columns(2)
                    with c1:
                        st.button("💰 Record New Payment")
                    with c2:
                        st.button("🧾 Generate Receipt")




    # 3. DASHBOARD CONTENT (The rest of your code)
    # This code will only execute if the user IS logged in
    st.write("Welcome to your dashboard!")
    # ... (Your PDF generation, image upload, and payment features go here)

st.subheader("Add Property Photos")
uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Display the image preview
    st.image(uploaded_file, caption="Uploaded Image", use_column_width=True)

    if st.button("Upload to RentEasy"):
        # Replace 'prop_123' with the actual ID from your database
        path = upload_property_image(uploaded_file, "prop_123")
        if path:
            st.success("Image uploaded successfully!")
        else:
            st.error("Upload failed. Check your storage policy.")

# Mock data (you would replace this with actual data from Supabase)
tenant = "John Doe"
amount = "500"
date = "2026-06-16"

if st.button("Generate Receipt"):
    pdf_file = generate_receipt_pdf(tenant, amount, date)

    # Provide download button
    with open(pdf_file, "rb") as f:
        st.download_button(
            label="Download PDF Receipt",
            data=f,
            file_name="receipt.pdf",
            mime="application/pdf"
        )




def get_access_token():
    consumer_key = st.secrets["mpesa"]["consumer_key"]
    consumer_secret = st.secrets["mpesa"]["consumer_secret"]
    api_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    response = requests.get(api_url, auth=(consumer_key, consumer_secret))
    return response.json().get("access_token")

def get_stk_password():
    shortcode = "174379"
    # Use the passkey from the Daraja portal
    passkey = "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919"
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    data_to_encode = shortcode + passkey + timestamp
    password = base64.b64encode(data_to_encode.encode()).decode()
    return timestamp, password

# --- CONFIGURATION & DIRECTORY SETUP ---
st.set_page_config(page_title="RentEasy Pro", layout="wide", page_icon="🏢")

UPLOAD_DIR = "lease_documents"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# CLOUD-SAFE DATABASE PATH: This keeps your data alive permanently on Streamlit Cloud!
DB_FILE = os.path.expanduser("~/.property_management_persistent.db")


def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS properties
                 (
                     id
                     INTEGER
                     PRIMARY
                     KEY
                     AUTOINCREMENT,
                     name
                     TEXT
                     NOT
                     NULL,
                     type
                     TEXT,
                     rent
                     REAL,
                     status
                     TEXT
                     DEFAULT
                     'Available'
                 )''')
    c.execute('''CREATE TABLE IF NOT EXISTS tenants
    (
        id
        INTEGER
        PRIMARY
        KEY
        AUTOINCREMENT,
        name
        TEXT
        NOT
        NULL,
        phone
        TEXT,
        email
        TEXT,
        property_id
        INTEGER
        UNIQUE,
        lease_doc_path
        TEXT,
        FOREIGN
        KEY
                 (
        property_id
                 ) REFERENCES properties
                 (
                     id
                 )
        )''')
    c.execute('''CREATE TABLE IF NOT EXISTS payments
    (
        id
        INTEGER
        PRIMARY
        KEY
        AUTOINCREMENT,
        property_id
        INTEGER,
        tenant_name
        TEXT,
        amount_paid
        REAL,
        payment_date
        TEXT,
        month_for
        TEXT,
        FOREIGN
        KEY
                 (
        property_id
                 ) REFERENCES properties
                 (
                     id
                 )
        )''')
    conn.commit()
    conn.close()


def run_query(query, params=(), target_table=None):
    init_db()
    with sqlite3.connect(DB_FILE) as conn:
        # FIXED: Explicitly passing params keyword to avoid index_col bugs!
        df = pd.read_sql_query(query, conn, params=params)

        if df.empty:
            if target_table == 'properties':
                return pd.DataFrame(columns=['id', 'name', 'type', 'rent', 'status'])
            elif target_table == 'tenants':
                return pd.DataFrame(columns=['id', 'name', 'phone', 'email', 'property_id', 'lease_doc_path'])
            elif target_table == 'payments':
                return pd.DataFrame(
                    columns=['id', 'property_id', 'tenant_name', 'amount_paid', 'payment_date', 'month_for'])
        return df


def run_action(query, params=()):
    init_db()
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute(query, params)
        conn.commit()


# --- SIDEBAR NAVIGATION ---
st.sidebar.title("🏢 RentEasy Pro")
st.sidebar.markdown("*Property & Rental Dashboard*")
st.sidebar.markdown("---")
menu = st.sidebar.radio("Navigation Menu", [
    "📊 Financial Reports",
    "🏠 Manage Properties",
    "👤 Manage Tenants",
    "💰 Rent Tracker & Reminders",
    "📁 Lease Document Vault",
    "Pay Rent"
])

if menu == "Pay Rent":
  st.subheader("Rent Payment Portal")
phone = st.text_input("M-Pesa Phone Number (e.g., 2547XXXXXXXX)", value="254")
amount = st.number_input("Rent Amount", min_value=1.0)

if st.button("Pay Now"):
    token = get_access_token()
    if token:
        st.success("Authentication Successful!")
        timestamp, password = get_stk_password()  # Ensure you have this function at the top
        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "BusinessShortCode": "174379",
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": int(amount),
            "PartyA": phone,
            "PartyB": "174379",
            "PhoneNumber": phone,
            "CallBackURL": "https://mydomain.com/callback",
            "AccountReference": "RentPayment",
            "TransactionDesc": "Rent Payment"
        }



        response = requests.post("https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest",
                                 json=payload, headers=headers)

        if response.status_code == 200:
            try:
                supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

                supabase.table("payments").insert({
                    "phone_number": str(phone),
                    "amount": float(amount),
                    "status": "pending"
                }).execute()

                st.success("Transaction recorded in database!")
                st.success("STK Push sent successfully! Check your phone.")

            except Exception as e:
                st.error(f"Database error: {e}")

        elif response.status_code == 401:
            # This handles the "Authentication Failed" specifically
            st.error("Authentication Failed! Please check your M-Pesa credentials.")

        else:
            # This handles other general failures
            st.error(f"Failed to initiate payment: {response.text}")




# ==========================================
# 1. FINANCIAL REPORTS
# ==========================================
if menu == "📊 Financial Reports":
    st.title("📊 Financial & Operational Reports")

    df_props = run_query("SELECT * FROM properties", target_table='properties')
    df_payments = run_query("SELECT * FROM payments", target_table='payments')

    if df_props.empty:
        st.info("👋 Welcome to RentEasy Pro! Your property portfolio is currently empty.")
        st.markdown("---")
        st.subheader("💡 Get Started in 2 Steps:")
        st.markdown("""
        1. Go to the **🏠 Manage Properties** menu on the left sidebar and add your first rental unit.
        2. Go to the **👤 Manage Tenants** menu to assign a tenant to that unit!
        """)
    else:
        total_units = len(df_props)
        occupied_units = len(df_props[df_props['status'] == 'Rented']) if 'status' in df_props.columns else 0
        occupancy_rate = (occupied_units / total_units) * 100 if total_units > 0 else 0

        expected_monthly = df_props[df_props['status'] == 'Rented'][
            'rent'].sum() if 'status' in df_props.columns else 0.0
        total_collected = df_payments['amount_paid'].sum() if not df_payments.empty else 0.0

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Managed Houses", total_units)
        col2.metric("Occupancy Rate", f"{occupancy_rate:.1f}%")
        col3.metric("Expected Monthly Rent", f"${expected_monthly:,.2f}")
        col4.metric("Total Collected To Date", f"${total_collected:,.2f}")

        st.markdown("---")

        col_left, col_right = st.columns(2)
        with col_left:
            st.subheader("📋 Property Overview")
            st.dataframe(df_props, use_container_width=True, hide_index=True)

        with col_right:
            st.subheader("📈 Revenue Collection History")
            if not df_payments.empty and 'month_for' in df_payments.columns:
                monthly_chart = df_payments.groupby("month_for")["amount_paid"].sum().reset_index()
                st.bar_chart(data=monthly_chart, x="month_for", y="amount_paid")
            else:
                st.caption("No rent payments logged yet.")

# ==========================================
# 2. MANAGE PROPERTIES
# ==========================================
elif menu == "🏠 Manage Properties":
    st.title("🏠 Property Portfolio Directory")

    col_form, col_view = st.columns([1, 2])

    with col_form:
        st.subheader("List New House")
        with st.form("add_house_form", clear_on_submit=True):
            h_name = st.text_input("Unit Identifier/Address", placeholder="e.g., Apartment 4B")
            h_type = st.selectbox("Property Type", ["Apartment", "Townhouse", "Studio Suite", "Commercial Office"])
            h_rent = st.number_input("Monthly Rent ($)", min_value=0.0, step=50.0)

            submit = st.form_submit_button("List House")
            if submit:
                if h_name:
                    run_action("INSERT INTO properties (name, type, rent) VALUES (?, ?, ?)", (h_name, h_type, h_rent))
                    st.success(f"Listed {h_name} successfully!")
                    st.rerun()

    with col_view:
        st.subheader("Current Inventory")
        df_view = run_query(
            "SELECT id AS 'House ID', name AS 'Address', type AS 'Type', rent AS 'Rent ($)', status AS 'Status' FROM properties",
            target_table='properties')
        if df_view.empty:
            st.caption("No houses listed yet.")
        else:
            st.dataframe(df_view, use_container_width=True, hide_index=True)

# ==========================================
# 3. MANAGE TENANTS
# ==========================================
elif menu == "👤 Manage Tenants":
    st.title("👤 Tenant Management Portal")

    vacant_houses = run_query("SELECT id, name FROM properties WHERE status = 'Available'", target_table='properties')
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Onboard New Tenant")
        if vacant_houses.empty:
            st.warning("No vacant units available. List a new house first.")
        else:
            with st.form("onboard_tenant_form", clear_on_submit=True):
                t_name = st.text_input("Tenant Name")
                t_phone = st.text_input("Phone Number")
                t_email = st.text_input("Email")

                house_options = {row['name']: row['id'] for _, row in vacant_houses.iterrows()}
                chosen_house_name = st.selectbox("Assign Unit", list(house_options.keys()))

                if st.form_submit_button("Sign Lease"):
                    chosen_id = house_options[chosen_house_name]
                    run_action("INSERT INTO tenants (name, phone, email, property_id) VALUES (?, ?, ?, ?)",
                               (t_name, t_phone, t_email, chosen_id))
                    run_action("UPDATE properties SET status = 'Rented' WHERE id = ?", (chosen_id,))
                    st.success(f"Assigned {t_name} to {chosen_house_name}!")
                    st.rerun()

    with col2:
        st.subheader("Active Occupant Directory")
        df_active = run_query("""
                              SELECT tenants.id AS 'Tenant ID', tenants.name AS 'Name', tenants.phone AS 'Phone', properties.name AS 'Unit', properties.rent AS 'Rent ($)'
                              FROM tenants
                                       JOIN properties ON tenants.property_id = properties.id
                              """, target_table='tenants')

        if df_active.empty or 'Name' not in df_active.columns:
            st.caption("No active tenants found.")
        else:
            st.dataframe(df_active, use_container_width=True, hide_index=True)

            st.markdown("---")
            st.subheader("⚠️ Lease Termination")
            tenant_mapping = {row['Name'] + " (" + row['Unit'] + ")": row['Tenant ID'] for _, row in
                              df_active.iterrows()}
            selected_termination = st.selectbox("Select Tenant to Move-Out", list(tenant_mapping.keys()))

            if st.button("Process Move-Out", type="primary"):
                t_id = tenant_mapping[selected_termination]
                p_id_res = run_query("SELECT property_id FROM tenants WHERE id = ?", (t_id,), target_table='tenants')
                if not p_id_res.empty:
                    p_id = int(p_id_res.iloc[0]['property_id'])
                    run_action("UPDATE properties SET status = 'Available' WHERE id = ?", (p_id,))
                    run_action("DELETE FROM tenants WHERE id = ?", (t_id,))
                    st.success("Lease closed. Unit is now available.")
                    st.rerun()

# ==========================================
# 4. RENT TRACKER & REMINDERS
# ==========================================
elif menu == "💰 Rent Tracker & Reminders":
    st.title("💰 Rent Collections & Reminders")

    occupied = run_query("""
                         SELECT tenants.name    AS tenant_name,
                                properties.id   AS prop_id,
                                properties.name AS prop_name,
                                properties.rent
                         FROM tenants
                                  JOIN properties ON tenants.property_id = properties.id
                         """, target_table='tenants')

    tab_pay, tab_remind = st.tabs(["💵 Log Rent Payment", "✉️ Send Reminders"])

    with tab_pay:
        if occupied.empty or 'tenant_name' not in occupied.columns:
            st.info("No occupied properties to log rent for.")
        else:
            with st.form("payment_form", clear_on_submit=True):
                pay_map = {row['prop_name'] + " - " + row['tenant_name']: row for _, row in occupied.iterrows()}
                selected_pay_unit = st.selectbox("Select Tenant", list(pay_map.keys()))

                target_data = pay_map[selected_pay_unit]
                amount = st.number_input("Amount Paid ($)", min_value=0.0, value=float(target_data['rent']))
                month = st.selectbox("Rent Month",
                                     ["January", "February", "March", "April", "May", "June", "July", "August",
                                      "September", "October", "November", "December"])
                date_str = st.date_input("Payment Date", value=datetime.today())

                if st.form_submit_button("Record Payment"):
                    run_action(
                        "INSERT INTO payments (property_id, tenant_name, amount_paid, payment_date, month_for) VALUES (?, ?, ?, ?, ?)",
                        (int(target_data['prop_id']), target_data['tenant_name'], amount, str(date_str), month))
                    st.success(f"Payment logged for {target_data['tenant_name']}.")
                    st.rerun()

        st.subheader("Payment Logs")
        df_hist = run_query(
            "SELECT tenant_name AS 'Tenant', amount_paid AS 'Paid ($)', payment_date AS 'Date', month_for AS 'Month' FROM payments ORDER BY id DESC",
            target_table='payments')
        if df_hist.empty or 'Tenant' not in df_hist.columns:
            st.caption("No payments recorded yet.")
        else:
            st.dataframe(df_hist, use_container_width=True, hide_index=True)

    with tab_remind:
        st.subheader("Generate Rent Reminder")
        if occupied.empty or 'tenant_name' not in occupied.columns:
            st.write("No active tenants found.")
        else:
            remind_map = {row['tenant_name'] + " (" + row['prop_name'] + ")": row for _, row in occupied.iterrows()}
            selected_remind = st.selectbox("Target Tenant", list(remind_map.keys()))
            tenant_info = remind_map[selected_remind]

            reminder_text = (
                f"Dear {tenant_info['tenant_name']},\n\n"
                f"This is a friendly reminder that rent of ${tenant_info['rent']:.2f} "
                f"for your unit '{tenant_info['prop_name']}' is currently due.\n\n"
                f"Please arrange for payment at your earliest convenience. If you have already paid, thank you, and please ignore this message.\n\n"
                f"Best regards,\nProperty Management"
            )
            st.text_area("Copy-paste ready text:", value=reminder_text, height=180)

# ==========================================
# 5. LEASE DOCUMENT VAULT
# ==========================================
elif menu == "📁 Lease Document Vault":
    st.title("📁 Lease Document Vault")

    tenants_list = run_query("SELECT id, name FROM tenants", target_table='tenants')

    if tenants_list.empty or 'name' not in tenants_list.columns:
        st.warning("No active tenants registered yet.")
    else:
        col_up, col_down = st.columns(2)
        with col_up:
            st.subheader("Upload Lease Contract")
            t_opts = {row['name']: row['id'] for _, row in tenants_list.iterrows()}
            chosen_doc_tenant = st.selectbox("Select Tenant Account:", list(t_opts.keys()))
            uploaded_file = st.file_uploader("Upload PDF / Lease Image", type=['pdf', 'png', 'jpg', 'jpeg'])

            if st.button("Save Document"):
                if uploaded_file is not None:
                    file_extension = os.path.splitext(uploaded_file.name)[1]
                    saved_filename = f"tenant_{t_opts[chosen_doc_tenant]}{file_extension}"
                    full_dest_path = os.path.join(UPLOAD_DIR, saved_filename)

                    with open(full_dest_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())

                    run_action("UPDATE tenants SET lease_doc_path = ? WHERE id = ?",
                               (full_dest_path, t_opts[chosen_doc_tenant]))
                    st.success(f"Saved contract for {chosen_doc_tenant}!")
                else:
                    st.error("Please upload a file.")

        with col_down:
            st.subheader("Vault Inventory")
            df_vault = run_query("SELECT name AS 'Tenant Name', lease_doc_path AS 'Storage Location' FROM tenants",
                                 target_table='tenants')
            if df_vault.empty or 'Tenant Name' not in df_vault.columns:
                st.caption("No documents in vault.")
            else:
                st.dataframe(df_vault, use_container_width=True, hide_index=True)

