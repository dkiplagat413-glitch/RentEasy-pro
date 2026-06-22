
import streamlit as st
import requests
import base64
from datetime import datetime
from supabase import create_client, Client
from utils import generate_receipt_pdf, upload_property_image,generate_lease_pdf
from email_utils import send_payment_confirmation, send_maintenance_update

from tenant import show_dashboard as tenant_dashboard
from landlord import show_dashboard as landlord_dashboard


# 1. Setup
st.set_page_config(page_title="RentEasy Pro", layout="wide", page_icon="🏢")
st.markdown("""
<style>
    .stApp {
        background-color: #f0f7f0;
    }
    [data-testid="stSidebar"] {
        background-color: #1a5c2a;
    }
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    h1, h2, h3 {
        color: #1a5c2a !important;
    }
    [data-testid="stMetric"] {
        background-color: white;
        border: 2px solid #1a5c2a;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 2px 2px 8px rgba(0,0,0,0.1);
    }
    [data-testid="stMetricValue"] {
        color: #1a5c2a !important;
        font-weight: bold !important;
    }
    .stButton > button {
        background-color: #1a5c2a !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: bold !important;
    }
    .stButton > button:hover {
        background-color: #2d8a42 !important;
    }
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input {
        border: 2px solid #1a5c2a !important;
        border-radius: 8px !important;
    }
    .stSelectbox > div > div {
        border: 2px solid #1a5c2a !important;
        border-radius: 8px !important;
    }
</style>
""", unsafe_allow_html=True)

url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
service_key = st.secrets["SUPABASE_SERVICE_KEY"]

supabase = create_client(url, key)
supabase_admin = create_client(url, service_key)



if "session" in st.session_state and st.session_state["session"]:
    supabase.auth.set_session(
        st.session_state["session"].access_token,
        st.session_state["session"].refresh_token
    )



# 2. Helper functions (defined before use)
def login_user(email, password):
    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        return response
    except Exception as e:
        return e


def get_access_token():
    consumer_key = st.secrets["mpesa"]["consumer_key"]
    consumer_secret = st.secrets["mpesa"]["consumer_secret"]
    api_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    response = requests.get(api_url, auth=(consumer_key, consumer_secret))
    return response.json().get("access_token")


def get_stk_password():
    shortcode = "174379"
    passkey = "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919"
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    data_to_encode = shortcode + passkey + timestamp
    password = base64.b64encode(data_to_encode.encode()).decode()
    return timestamp, password


# 3. Session state init
if "user" not in st.session_state:
    st.session_state["user"] = None

# 4. Auth gate — nothing below this block runs unless the user is logged in
if st.session_state.get("user") is None:



    menu = st.sidebar.selectbox("Menu", ["Login", "Sign Up"])

    if menu == "Login":
        st.markdown("<h3 style='color: #1a5c2a; text-align: center;'>🔐 Login to Your Account</h3>",
                    unsafe_allow_html=True)

        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")

        if st.button("Submit", key="login_btn"):
            result = login_user(email, password)
            if hasattr(result, "user") and result.user:
                st.session_state["user"] = result.user
                st.session_state["session"] = result.session
                supabase.auth.set_session(result.session.access_token, result.session.refresh_token)
                st.success("Logged in successfully!")
                st.rerun()
            else:
                st.error("Login failed. Check your credentials.")

    elif menu == "Sign Up":
        st.subheader("Create New Account")
        new_email = st.text_input("Email", key="signup_email")
        new_password = st.text_input("Password", type="password", key="signup_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")

        new_role = "tenant"

        if st.button("Register", key="signup_btn"):
            if new_password != confirm_password:
                st.error("Passwords do not match!")
            else:
                try:
                    result = supabase.auth.sign_up({"email": new_email, "password": new_password})
                    if result.user:
                        supabase.table("profiles").insert({
                            "id": result.user.id,
                            "email": new_email,
                            "role": new_role
                        }).execute()
                    st.success("Account created! Please navigate to the Login page.")
                except Exception as e:
                    st.error(f"Error: {e}")

    st.stop()

# --- everything below only runs if the user IS logged in ---
st.title("RentEasy Pro")
user_id = st.session_state["user"].id
profile = supabase.table("profiles").select("role").eq("id", user_id).execute().data

user_role = profile[0]["role"] if profile else "tenant"




with st.sidebar:
    st.title("RentEasy Pro")

    if user_role == "landlord":
        nav_options = ["Dashboard", "Properties", "Tenants", "Payments", "Reports","Lease Agreements"]
    else:
        nav_options = ["Dashboard", "Properties", "My Bookings", "Pay Rent", "Maintenance"]

    page = st.radio(label="Navigation", options=nav_options)
    st.divider()
    if st.button("Logout"):
        st.session_state["user"] = None
        st.session_state["session"] = None
        st.rerun()
    st.divider()
    st.markdown(f"📧 **{st.session_state['user'].email}**")
# 5. Page router
if page == "Dashboard":
    st.header("Dashboard")
    user_email = st.session_state["user"].email

    if user_role == "landlord":
        props = supabase.table("properties").select("*").execute().data
        maintenance = supabase.table("maintenance_request") \
            .select("*").eq("status", "Pending").execute().data
        payments_data = supabase.table("payments").select("amount, status").execute().data
        revenue = sum([p.get("amount", 0) for p in payments_data if p.get("status") == "completed"])

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Properties", len(props))
        col2.metric("Occupied", len([p for p in props if p.get("status") == "Booked"]))
        col3.metric("Pending Maintenance", len(maintenance))
        col4.metric("Revenue (KES)", f"KES {revenue:,.0f}")
        st.divider()
        st.info("Use the sidebar to manage your properties and tenants.")

    else:
        bookings = supabase.table("properties") \
            .select("*").eq("booked_by", user_email).execute().data
        requests = supabase.table("maintenance_request") \
            .select("*").eq("tenant_email", user_email).execute().data

        col1, col2 = st.columns(2)
        col1.metric("My Bookings", len(bookings))
        col2.metric("My Maintenance Requests", len(requests))
        st.divider()

        if bookings:
            st.subheader("My Current Properties")
            for b in bookings:
                st.write(f"🏠 **{b.get('name')}** — Status: {b.get('status')}")
        else:
            st.info("You have no active bookings. Go to Properties to book one.")


elif page == "Properties":
    st.header("🏠 Properties")
    if user_role == "landlord":
        with st.expander("➕ Add New Property"):
            new_name = st.text_input("Property Name", key="new_prop_name")
            new_location = st.text_input(
                label="Location (e.g. Westlands, Nairobi)",
                key="new_prop_location"
            )

            new_description = st.text_area("Description", key="new_prop_desc")
            new_price = st.number_input("Monthly Rent (KES)", min_value=0, key="new_prop_price")
            new_image = st.file_uploader("Property Photo", type=["jpg", "jpeg", "png"], key="new_prop_img")
            new_video = st.file_uploader(
                "Property Video Tour (optional)",
                type=["mp4", "mov", "avi"],
                key="prop_video"
            )

            if st.button("Add Property", key="add_prop_btn"):
                if not new_name:
                    st.error("Property name is required.")
                else:
                    image_url = None
                    if new_image:
                        image_url = upload_property_image(new_image, new_name)
                        st.write(f"DEBUG image_url: {image_url}")

                    video_url = None
                    if new_video:
                        video_bytes = new_video.getvalue()
                        video_path = f"{new_name.replace(' ', '_')}_video.mp4"
                        supabase.storage.from_("property-images").upload(
                            path=video_path,
                            file=video_bytes,
                            file_options={"content-type": "video/mp4", "upsert": "true"}
                        )
                        video_url = supabase.storage.from_("property-images").get_public_url(video_path)

                    supabase.table("properties").insert({
                        "name": new_name,
                        "description": new_description,
                        "price": new_price,
                        "status": "Available",
                        "image_url": image_url,
                        "video_url": video_url,
                        "location": new_location
                    }).execute()
                    st.success(f"Property '{new_name}' added successfully!")
                    st.rerun()

    col1, col2, col3, col4 = st.columns(4)
    all_properties = supabase_admin.table("properties").select("*").execute().data
    total = len(all_properties)
    occupied = len([p for p in all_properties if p.get("status") == "Booked"])
    available = total - occupied
    payments_data = supabase.table("payments").select("amount").execute().data
    revenue = sum([p.get("amount", 0) for p in payments_data])

    col1.metric("Total Properties", total)
    col2.metric("Occupied", occupied)
    col3.metric("Available", available)
    col4.metric("Revenue (KES)", f"KES {revenue:,.0f}")

    st.subheader("Property Portfolio")
    search_query = st.text_input("Search by name...")
    location_filter = st.selectbox("Filter by County", [
        "All Counties", "Nairobi", "Mombasa", "Kisumu", "Nakuru",
        "Eldoret", "Thika", "Malindi", "Kitale", "Garissa", "Nyeri",
        "Meru", "Machakos", "Kakamega", "Kisii", "Kericho"
    ])

    properties = all_properties


    if search_query:
        properties = [p for p in properties if search_query.lower() in p.get("name", "").lower()]


    if location_filter != "All Counties":
            properties = [p for p in properties if location_filter.lower() in p.get("location", "").lower()]
    if properties:
            cols = st.columns(3)
            for i, prop in enumerate(properties):
                with cols[i % 3]:
                    image_url = prop.get("image_url")
                    if image_url:
                        st.image(image_url, width=250)
                    else:
                        st.write("No image available")
                        st.write(f"📍 {prop.get('location', 'Location not specified')}")

                    video_url = prop.get("video_url")
                    if video_url:
                        st.video(video_url)

                    st.write(f"**{prop.get('name', 'Unknown')}**")
                    st.write(f"Status: {prop.get('status', 'N/A')}")

                    if prop.get("status") == "Available":
                        if st.button(f"Book {prop.get('name')}", key=f"book_{prop.get('id')}"):
                            result = supabase.table("properties") \
                                .update({"status": "Booked", "booked_by": st.session_state["user"].email}) \
                                .eq("id", prop.get("id")) \
                                .execute()
                            st.rerun()
                    else:
                        st.write("🔴 Already Booked")

                    if user_role == "landlord":
                        if st.button(f"🗑️ Delete {prop.get('name')}", key=f"delete_{prop.get('id')}"):
                            supabase.table("properties") \
                                .delete() \
                                .eq("id", prop.get("id")) \
                                .execute()
                            st.success(f"Property deleted.")
                            st.rerun()


    else:
        st.info("No properties found in database.")

elif page == "Tenants":
    if user_role != "landlord":
        st.error("You don't have access to this page.")
        st.stop()
    st.header("Tenants")
    tenants = supabase.table("properties").select("*").not_.is_("booked_by", "null").execute().data
    if tenants:
        for t in tenants:
            with st.container(border=True):
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.write(f"**Property:** {t.get('name')}")
                    st.write(f"**Tenant:** {t.get('booked_by')}")
                with col2:
                    st.write(f"Status: {t.get('status')}")
                    if t.get('price'):
                        st.write(f"Rent: KES {t.get('price'):,}")
    else:
        st.info("No active tenants yet.")

elif page == "Maintenance":
    st.header("Maintenance Request")
    st.subheader("Report an Issue")

    user_properties = supabase.table("properties") \
        .select("*") \
        .eq("booked_by", st.session_state["user"].email) \
        .execute().data

    if user_properties:
        property_names = {p["name"]: p["id"] for p in user_properties}
        selected_property = st.selectbox("Which property?", list(property_names.keys()))
        description = st.text_area("Describe the issue")

        if st.button("Submit Request"):
            supabase.table("maintenance_request").insert({
                "property_id": property_names[selected_property],
                "description": description,
                "status": "Pending",
                "tenant_email": st.session_state["user"].email
            }).execute()
            st.success("Request submitted!")
            st.rerun()
    else:
        st.info("You need an active booking to submit a maintenance request.")

    st.divider()
    st.subheader("Your Past Requests")
    my_requests = supabase.table("maintenance_request") \
        .select("*, properties(name)") \
        .eq("tenant_email", st.session_state["user"].email) \
        .execute().data

    if my_requests:
        for req in my_requests:
            prop_name = req.get("properties", {}).get("name", "Unknown")
            st.write(f"**{prop_name}** — {req.get('description')}")
            st.write(f"Status: {req.get('status', 'Pending')}")
            st.divider()
    else:
        st.info("No maintenance requests yet.")

elif page == "Payments":
    if user_role != "landlord":
        st.error("You don't have access to this page.")
        st.stop()

    st.header("💰 Payments Overview")

    all_payments = supabase.table("payments").select("*").execute().data

    completed = [p for p in all_payments if p.get("status") == "completed"]
    pending = [p for p in all_payments if p.get("status") == "pending"]

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Revenue (KES)", f"{sum(p.get('amount', 0) for p in completed):,.0f}")
    col2.metric("Completed Payments", len(completed))
    col3.metric("Pending Payments", len(pending))

    st.divider()

    filter_status = st.selectbox("Filter by Status", ["All", "completed", "pending", "failed"])
    filtered = [p for p in all_payments if
                p.get("status") == filter_status] if filter_status != "All" else all_payments

    st.subheader(f"Payment Records ({len(filtered)})")

    if filtered:
        for p in filtered:
            with st.container(border=True):
                col1, col2, col3, col4 = st.columns(4)
                col1.write(f"**Tenant:** {p.get('tenant_email', 'Unknown')}")
                col2.write(f"**Amount:** KES {p.get('amount', 0):,.0f}")
                status = p.get('status', 'Unknown')
                if status == 'completed':
                    col3.markdown("**Status:** :green[✅ Completed]")
                elif status == 'pending':
                    col3.markdown("**Status:** :orange[⏳ Pending]")
                elif status == 'failed':
                    col3.markdown("**Status:** :red[❌ Failed]")
                date = p.get('created_at', '')[:10] if p.get('created_at') else '-'
                col4.write(f"**Date:** {date}")
    else:
        st.info("No payment records found.")


elif page == "Pay Rent":
    st.header("Pay Rent")
    st.subheader("Pay Rent (M-Pesa)")

    # Init session state for receipt
    if "last_receipt" not in st.session_state:
        st.session_state["last_receipt"] = None

    phone = st.text_input("M-Pesa Phone Number (e.g., 2547XXXXXXXX)", value="254")
    pay_amount = st.number_input("Rent Amount", min_value=1.0)

    if st.button("Pay Now"):
        token = get_access_token()
        if token:
            timestamp, password = get_stk_password()
            headers = {"Authorization": f"Bearer {token}"}
            payload = {
                "BusinessShortCode": "174379",
                "Password": password,
                "Timestamp": timestamp,
                "TransactionType": "CustomerPayBillOnline",
                "Amount": int(pay_amount),
                "PartyA": phone,
                "PartyB": "174379",
                "PhoneNumber": phone,
                "CallBackURL": "https://mpesa-callback-bddq.onrender.com/callback",
                "AccountReference": "RentPayment",
                "TransactionDesc": "Rent Payment"
            }
            response = requests.post(
                "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest",
                json=payload, headers=headers
            )

            if response.status_code == 200:
                try:
                    supabase.table("payments").insert({
                        "phone_number": str(phone),
                        "amount": float(pay_amount),
                        "status": "pending",
                        "tenant_email": st.session_state["user"].email
                    }).execute()
                    st.success("✅ STK Push sent! Check your phone and enter PIN.")
                    send_payment_confirmation(
                        st.session_state["user"].email,
                        int(pay_amount),
                        datetime.now().strftime("%Y-%m-%d")
                    )

                    # Store receipt data in session state so it survives rerun
                    tenant_name = st.session_state["user"].email
                    date_str = datetime.now().strftime("%Y-%m-%d")
                    pdf_file = generate_receipt_pdf(tenant_name, str(int(pay_amount)), date_str)
                    with open(pdf_file, "rb") as f:
                        st.session_state["last_receipt"] = {
                            "data": f.read(),
                            "filename": f"RentEasy_Receipt_{date_str}.pdf"
                        }
                except Exception as e:
                    st.error(f"Database error: {e}")
            else:
                st.error(f"Failed to initiate payment: {response.text}")
        else:
            st.error("Could not authenticate with M-Pesa. Check your credentials.")

    # Always show receipt download if available
    if st.session_state.get("last_receipt"):
        st.success("✅ Payment initiated!")
        st.download_button(
            label="📄 Download Receipt",
            data=st.session_state["last_receipt"]["data"],
            file_name=st.session_state["last_receipt"]["filename"],
            mime="application/pdf",
            key="receipt_download"
        )

    # ✅ Payment history is NOW outside the button block — always visible
    st.divider()
    st.subheader("My Payment History")

    payment_history = supabase.table("payments") \
        .select("*") \
        .eq("tenant_email", st.session_state["user"].email) \
        .execute().data

    if payment_history:
        for payment in payment_history:
            with st.container(border=True):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"**Amount:** KES {payment.get('amount', 0):,.0f}")
                with col2:
                    status = payment.get('status', 'Unknown')
                    if status == 'completed':
                        st.markdown("**Status:** :green[✅ Completed]")
                    elif status == 'pending':
                        st.markdown("**Status:** :orange[⏳ Pending]")
                    elif status == 'failed':
                        st.markdown("**Status:** :red[❌ Failed]")

                with col3:
                    created = payment.get('created_at', '')
                    if created:
                        st.write(f"**Date:** {created[:10]}")
    else:
        st.info("No payment history yet.")



elif page == "My Bookings":
    st.header("My Reservations")
    user_email = st.session_state["user"].email
    booked_properties = supabase.table("properties") \
        .select("*") \
        .eq("booked_by", user_email) \
        .execute().data

    if booked_properties:
        for prop in booked_properties:
            st.image(prop.get("image_url"), width=250)

            st.write(f"### {prop.get('name')}")
            st.write(f"Status: **{prop.get('status')}**")

            if st.button(f"Cancel Booking {prop.get('name')}", key=f"cancel_{prop.get('id')}"):
                supabase.table("properties") \
                    .update({"status": "Available", "booked_by": None}) \
                    .eq("id", prop.get("id")) \
                    .execute()
                st.rerun()
    else:
        st.info("You haven't booked any properties yet.")

elif page == "Reports":
    if user_role != "landlord":
        st.error("You don't have access to this page.")
        st.stop()
    st.header("🔧 Maintenance Requests")

    requests = supabase.table("maintenance_request") \
        .select("*, properties(name)") \
        .execute().data

    if requests:
        for req in requests:
            prop_name = req.get("properties", {}).get("name", "Unknown Property")
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**Property:** {prop_name}")
                    st.write(f"**Issue:** {req.get('description', 'No description')}")
                    st.write(f"**Reported by:** {req.get('tenant_email', 'Unknown')}")
                with col2:
                    status = req.get('status', 'Pending')
                    if status == 'Resolved':
                        st.markdown(":green[✅ Resolved]")
                        send_maintenance_update(
                            req.get("tenant_email"),
                            req.get("description"),
                            "Resolved"
                        )

                    else:
                        st.markdown(":orange[⏳ Pending]")

                        if st.button(label="Mark Resolved", key=f"resolve_{req.get('id')}"):
                            supabase.table("maintenance_request") \
                                .update({"status": "Resolved"}) \
                                .eq("id", req.get("id")) \
                                .execute()

                            # Send email to tenant
                            send_maintenance_update(
                                req.get("tenant_email"),
                                req.get("description"),
                                "Resolved"
                            )
                            st.rerun()

    else:
        st.info("No maintenance requests yet.")

elif page == "Lease Agreements":
        st.header("📄 Lease Agreements")

        if user_role != "landlord":
            st.error("You don't have access to this page.")
        else:
            booked = supabase_admin.table("properties") \
                .select("*") \
                .eq("status", "Booked") \
                .execute().data

            st.subheader("Generate New Lease Agreement")

            with st.form("lease_form"):
                landlord_name = st.text_input("Landlord Full Name")
                landlord_phone = st.text_input("Landlord Phone")
                tenant_name = st.text_input("Tenant Full Name")
                tenant_phone = st.text_input("Tenant Phone")
                property_options = [p["name"] for p in booked] if booked else ["No booked properties"]
                selected_prop = st.selectbox("Select Property", property_options)
                property_address = st.text_input("Property Address/Location")
                monthly_rent = st.number_input("Monthly Rent (KES)", min_value=0.0)
                deposit_amount = st.number_input("Security Deposit (KES)", min_value=0.0)
                start_date = st.date_input("Lease Start Date")
                end_date = st.date_input("Lease End Date")
                submit = st.form_submit_button("Generate Lease Agreement")

            if submit:
                    file_path = generate_lease_pdf(
                        landlord_name=landlord_name,
                        landlord_phone=landlord_phone,
                        tenant_name=tenant_name,
                        tenant_phone=tenant_phone,
                        property_name=selected_prop,
                        property_address=property_address,
                        monthly_rent=monthly_rent,
                        deposit_amount=deposit_amount,
                        start_date=str(start_date),
                        end_date=str(end_date)
                    )
                    with open(file_path, "rb") as f:
                        st.download_button(
                            label="📥 Download Lease Agreement",
                            data=f,
                            file_name=f"Lease_{tenant_name}_{selected_prop}.pdf",
                            mime="application/pdf"
                        )
                    st.success(f"Lease generated for {tenant_name}!")


