import smtplib
from email.message import EmailMessage

from .security import settings


def send_login_notification(
    recipient_email: str,
    user_name: str,
) -> None:

    if not settings.MAIL_USERNAME or not settings.MAIL_PASSWORD:
        print("Email notification skipped: mail credentials are not configured.")
        return

    sender_email = settings.MAIL_FROM or settings.MAIL_USERNAME

    message = EmailMessage()
    message["Subject"] = "Mini Spotify - New Login Detected"
    message["From"] = sender_email
    message["To"] = recipient_email

    message.set_content(
        f"""Hello {user_name},

A login to your Mini Spotify account was detected.

If this was you, no action is required.

If you did not log in, please change your password immediately.

Regards,
Mini Spotify Security
"""
    )

    try:
        print("Connecting to Gmail SMTP...")

        with smtplib.SMTP(
            settings.MAIL_HOST,
            settings.MAIL_PORT,
            timeout=20,
        ) as server:

            server.set_debuglevel(1)

            print("Starting TLS...")
            server.starttls()

            print("Logging into Gmail...")
            server.login(
                settings.MAIL_USERNAME,
                settings.MAIL_PASSWORD,
            )

            print("Sending notification...")
            server.send_message(message)

        print(f"Login notification sent to {recipient_email}")

    except Exception as exc:
        print(f"Failed to send login notification: {type(exc).__name__}: {exc}")