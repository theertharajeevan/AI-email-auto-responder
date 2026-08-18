import os
import smtplib

from email.message import EmailMessage

from dotenv import load_dotenv


load_dotenv()


def send_email(
    recipient: str,
    subject: str,
    body: str,
) -> None:

    sender = os.getenv(
        "EMAIL_ADDRESS"
    )

    app_password = os.getenv(
        "APP_PASSWORD"
    )

    if not sender:

        raise ValueError(
            "EMAIL_ADDRESS is not configured."
        )

    if not app_password:

        raise ValueError(
            "APP_PASSWORD is not configured."
        )

    message = EmailMessage()

    message["From"] = sender

    message["To"] = recipient

    message["Subject"] = subject

    message.set_content(body)

    with smtplib.SMTP_SSL(
        "smtp.gmail.com",
        465,
    ) as server:

        server.login(
            sender,
            app_password,
        )

        server.send_message(
            message
        )