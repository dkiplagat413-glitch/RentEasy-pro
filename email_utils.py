import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import streamlit as st

def send_email(to_email, subject, body):
    try:
        sender = st.secrets["EMAIL_ADDRESS"]
        password = st.secrets["EMAIL_PASSWORD"]

        msg = MIMEMultipart()
        msg["From"] = sender
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.sendmail(sender, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False


def send_payment_confirmation(tenant_email, amount, date):
    subject = "✅ RentEasy Pro - Payment Confirmation"
    body = f"""
    <h2>Payment Received</h2>
    <p>Dear Tenant,</p>
    <p>Your payment of <strong>KES {amount}</strong> on <strong>{date}</strong> has been initiated successfully.</p>
    <p>Status will update to <strong>Completed</strong> once M-Pesa confirms.</p>
    <br>
    <p>Thank you for using <strong>RentEasy Pro</strong>!</p>
    """
    return send_email(tenant_email, subject, body)


def send_maintenance_update(tenant_email, issue, status):
    subject = "🔧 RentEasy Pro - Maintenance Update"
    body = f"""
    <h2>Maintenance Request Update</h2>
    <p>Dear Tenant,</p>
    <p>Your maintenance request: <strong>"{issue}"</strong></p>
    <p>Status has been updated to: <strong>{status}</strong></p>
    <br>
    <p>Thank you for using <strong>RentEasy Pro</strong>!</p>
    """
    return send_email(tenant_email, subject, body)


def send_rent_reminder(tenant_email, amount, due_date):
    subject = "⏰ RentEasy Pro - Rent Reminder"
    body = f"""
    <h2>Rent Due Reminder</h2>
    <p>Dear Tenant,</p>
    <p>This is a reminder that your rent of <strong>KES {amount}</strong> 
    is due on <strong>{due_date}</strong>.</p>
    <p>Please log in to RentEasy Pro to make your payment.</p>
    <br>
    <p><strong>RentEasy Pro</strong></p>
    """
    return send_email(tenant_email, subject, body)
