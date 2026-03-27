"""Quick test — sends one email to yourself to verify Gmail SMTP works."""

from config import GMAIL_ADDRESS, GMAIL_APP_PASSWORD
from emailer import send_email

if __name__ == "__main__":
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        print("ERROR: Set GMAIL_ADDRESS and GMAIL_APP_PASSWORD in .env first")
        exit(1)

    print(f"Sending test email from {GMAIL_ADDRESS} to {GMAIL_ADDRESS}...")

    try:
        send_email(
            sender=GMAIL_ADDRESS,
            app_password=GMAIL_APP_PASSWORD,
            to_address=GMAIL_ADDRESS,
            subject="Test — Supplier Discovery Tool",
            body="Hi {company_name},\n\nThis is a test email from the Supplier Discovery Tool.\n\nIf you received this, the email sending is working!\n\nBest regards",
        )
        print("SUCCESS — check your inbox!")
    except Exception as e:
        print(f"FAILED — {e}")
