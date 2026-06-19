
import streamlit as st

def show_dashboard(supabase):
    st.title("Tenant Dashboard")
    st.write("Welcome, Tenant! You can pay rent and request maintenance here.")

    menu = st.sidebar.radio("Menu", ["Pay Rent", "Payment History", "Maintenance Request"])

    if menu == "Pay Rent":
        show_pay_rent(supabase)
    elif menu == "Payment History":
        show_payment_history(supabase)
    elif menu == "Maintenance Request":
        show_maintenance(supabase)


def show_pay_rent(supabase):
    st.header("Pay Rent (M-Pesa)")

    phone = st.text_input("M-Pesa Phone Number (e.g., 2547XXXXXXXX)")
    amount = st.number_input("Rent Amount", min_value=1.0, step=1.0)

    if st.button("Pay Now"):
        if not phone or len(phone) < 10:
            st.error("Enter a valid phone number.")
            return

        tenant_email = st.session_state["user"].email

        # Save to Supabase
        supabase.table("payments").insert({
            "phone_number": phone,
            "amount": amount,
            "status": "pending",
            "tenant_email": tenant_email
        }).execute()

        st.success(f"Payment of KES {amount} initiated to {phone}. Check history for status.")


def show_payment_history(supabase):
    st.header("My Payment History")

    tenant_email = st.session_state["user"].email
    history = supabase.table("payments") \
        .select("*") \
        .eq("tenant_email", tenant_email) \
        .execute().data

    if not history:
        st.info("No payment records found.")
        return

    for payment in history:
        with st.container(border=True):
            col1, col2, col3 = st.columns(3)
            col1.write(f"**Amount:** KES {payment.get('amount', 0):.0f}")
            col2.write(f"**Status:** {payment.get('status', 'Unknown')}")
            col3.write(f"**Phone:** {payment.get('phone_number', '-')}")


def show_maintenance(supabase):
    st.header("Request Maintenance")

    issue = st.text_area("Describe the issue")

    if st.button("Submit Request"):
        if not issue:
            st.error("Please describe the issue.")
            return

        tenant_email = st.session_state["user"].email
        supabase.table("maintenance_request").insert({
            "tenant_email": tenant_email,
            "issue": issue,
            "status": "open"
        }).execute()

        st.success("Maintenance request submitted!")

