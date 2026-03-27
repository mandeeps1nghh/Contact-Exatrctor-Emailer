import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_email(sender, app_password, to_address, subject, body):
    """Send a single email via Gmail SMTP (SSL on port 465)."""
    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = to_address
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender, app_password)
        server.sendmail(sender, to_address, msg.as_string())


def send_bulk_emails(sender, app_password, recipients, subject, template):
    """
    Send bulk emails using a template.

    Args:
        recipients: list of dicts with "email" and "company_name" keys
        template: email body with {company_name} placeholder

    Returns:
        (success_count, failures_list)
    """
    success = 0
    failures = []

    context = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(sender, app_password)

            for r in recipients:
                email = r["email"]
                company = r.get("company_name", "")
                body = template.replace("{company_name}", company)

                try:
                    msg = MIMEMultipart()
                    msg["From"] = sender
                    msg["To"] = email
                    msg["Subject"] = subject.replace("{company_name}", company)
                    msg.attach(MIMEText(body, "plain"))

                    server.sendmail(sender, email, msg.as_string())
                    success += 1
                    print(f"  Sent to {email}")
                except Exception as e:
                    failures.append({"email": email, "error": str(e)})
                    print(f"  Failed: {email} — {e}")
    except Exception as e:
        print(f"SMTP connection error: {e}")
        if success == 0:
            failures.append({"email": "ALL", "error": str(e)})

    return success, failures
