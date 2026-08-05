"""Small provider-independent SMTP adapter for transactional messages."""

import smtplib
from collections.abc import Mapping
from email.message import EmailMessage
from typing import Any


def send_verification_email(config: Mapping[str, Any], recipient: str, token: str) -> None:
    """Send the one-time verification link without logging its token."""
    message = EmailMessage()
    message["Subject"] = "Activez votre compte Matcha"
    message["From"] = f'{config["SMTP_FROM_NAME"]} <{config["SMTP_FROM_EMAIL"]}>'
    message["To"] = recipient
    link = f'{str(config["FRONTEND_URL"]).rstrip("/")}/verify-email?token={token}'
    message.set_content(f"Bienvenue sur Matcha. Activez votre compte avec ce lien :\n{link}\n")

    with smtplib.SMTP(str(config["SMTP_HOST"]), int(config["SMTP_PORT"]), timeout=5) as smtp:
        if config["SMTP_USE_TLS"]:
            smtp.starttls()
        username = str(config["SMTP_USERNAME"])
        if username:
            smtp.login(username, str(config["SMTP_PASSWORD"]))
        smtp.send_message(message)
