import smtplib
import os
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from itsdangerous import URLSafeTimedSerializer

# Allow cleaner import from app context
def init_email_service(app):
    global serializer, BASE_URL, SMTP_EMAIL, SMTP_PASSWORD, SMTP_SERVER, SMTP_PORT
    serializer = URLSafeTimedSerializer(app.secret_key)
    BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:5000")
    SMTP_EMAIL = os.getenv("SMTP_EMAIL")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))

def send_approval_email(year, code, attachments=None):
    if not (SMTP_EMAIL and SMTP_PASSWORD):
        print("[EMAIL WARNING] SMTP credentials not set. Email skipped.")
        return

    token = serializer.dumps({"year": year, "code": code, "action": "approve"}, salt="approve-paper")
    approve_link = f"{BASE_URL}/api/approve_token/{token}"
    
    subject = f"GATE Predictor: New Submission {code} ({year})"
    body = f"""
    <h2>New Submission for Review</h2>
    <p>A new paper has been uploaded to the staging area.</p>
    <ul>
        <li><strong>Paper Code:</strong> {code}</li>
        <li><strong>Year:</strong> {year}</li>
    </ul>
    <p>
        <a href="{approve_link}" style="background:#10b981; color:white; padding:10px 20px; text-decoration:none; border-radius:5px;">
            Approve & Publish Live
        </a>
    </p>
    <p>Or visit the <a href="{BASE_URL}/dashboard">Admin Dashboard</a> to review.</p>
    """
    
    print(f"\n[EMAIL DEBUG] To Admin ({SMTP_EMAIL}):\nSubject: {subject}\nLink: {approve_link}\n")
    
    try:
        msg = MIMEMultipart()
        msg['From'] = f"GATE Predictor <{SMTP_EMAIL}>"
        msg['To'] = SMTP_EMAIL
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))
        
        # Attach files if provided
        # attachments: list of {'name': str, 'data': bytes}
        if attachments:
            for item in attachments:
                try:
                    name = item.get('name')
                    data = item.get('data')
                    if name and data:
                        part = MIMEApplication(data, Name=name)
                        part['Content-Disposition'] = f'attachment; filename="{name}"'
                        msg.attach(part)
                except Exception as ex:
                    print(f"[EMAIL ERROR] Failed to attach {item.get('name')}: {ex}")
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.send_message(msg)
        print("[EMAIL] Sent successfully.")
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send: {e}")

def send_approval_email_async(year, code, attachments=None):
    # Wrapper for threading
    thread = threading.Thread(target=send_approval_email, args=(year, code, attachments))
    thread.start()
