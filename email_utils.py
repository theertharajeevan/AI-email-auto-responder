import email
import imaplib
import os

from email.header import decode_header
from email.message import Message
from email.utils import parseaddr
from typing import Any

from dotenv import load_dotenv


load_dotenv()


# =========================================================
# HEADER DECODING
# =========================================================

def decode_mime_header(
    value: str | None,
) -> str:

    if not value:
        return ""

    decoded_parts = decode_header(value)

    result_parts = []

    for part, encoding in decoded_parts:

        if isinstance(part, bytes):

            result_parts.append(
                part.decode(
                    encoding or "utf-8",
                    errors="replace",
                )
            )

        else:

            result_parts.append(part)

    return " ".join(
        result_parts
    ).strip()


# =========================================================
# EMAIL BODY
# =========================================================

def parse_email_body(
    message: Message,
) -> str:

    if message.is_multipart():

        text_parts = []
        html_parts = []

        for part in message.walk():

            content_type = (
                part.get_content_type()
            )

            content_disposition = str(
                part.get(
                    "Content-Disposition",
                    "",
                )
            ).lower()

            # Ignore attachments
            if "attachment" in content_disposition:
                continue

            payload = part.get_payload(
                decode=True
            )

            if payload is None:
                continue

            charset = (
                part.get_content_charset()
                or "utf-8"
            )

            decoded_text = payload.decode(
                charset,
                errors="replace",
            )

            if content_type == "text/plain":

                text_parts.append(
                    decoded_text
                )

            elif content_type == "text/html":

                html_parts.append(
                    decoded_text
                )

        if text_parts:

            return "\n".join(
                text_parts
            ).strip()

        if html_parts:

            return html_parts[0].strip()

        return ""

    payload = message.get_payload(
        decode=True
    )

    if payload is None:
        return ""

    charset = (
        message.get_content_charset()
        or "utf-8"
    )

    return payload.decode(
        charset,
        errors="replace",
    ).strip()


# =========================================================
# PARSE EMAIL
# =========================================================

def parse_email_message(
    raw_email: bytes,
) -> dict[str, str]:

    message = email.message_from_bytes(
        raw_email
    )

    sender_header = decode_mime_header(
        message.get("From")
    )

    _, sender_email = parseaddr(
        sender_header
    )

    subject = decode_mime_header(
        message.get("Subject")
    )

    reply_to_header = decode_mime_header(
        message.get("Reply-To")
    )

    _, reply_to_email = parseaddr(
        reply_to_header
    )

    body = parse_email_body(
        message
    )

    return {
        "sender": sender_header,
        "sender_email": sender_email,

        "reply_to": reply_to_header,
        "reply_to_email": reply_to_email,

        "subject": subject or "(No subject)",

        "body": body or "(No body content)",
    }


# =========================================================
# FETCH UNREAD EMAILS
# =========================================================

def fetch_unread_emails(
    email_address: str | None = None,
    app_password: str | None = None,
    max_emails: int = 20,
) -> list[dict[str, Any]]:

    email_address = (
        email_address
        or os.getenv("EMAIL_ADDRESS")
    )

    app_password = (
        app_password
        or os.getenv("APP_PASSWORD")
    )

    if not email_address:
        raise ValueError(
            "EMAIL_ADDRESS is not configured in .env"
        )

    if not app_password:
        raise ValueError(
            "APP_PASSWORD is not configured in .env"
        )

    print(
        f"\nConnecting to Gmail account: "
        f"{email_address}"
    )

    mail = imaplib.IMAP4_SSL(
        "imap.gmail.com",
        993,
    )

    try:

        # -------------------------------------------------
        # LOGIN
        # -------------------------------------------------

        status, response = mail.login(
            email_address,
            app_password,
        )

        if status != "OK":

            raise RuntimeError(
                f"Gmail login failed: {response}"
            )

        print("Gmail login successful.")

        # -------------------------------------------------
        # SELECT INBOX
        # -------------------------------------------------

        status, mailbox_info = mail.select(
            "INBOX"
        )

        if status != "OK":

            raise RuntimeError(
                f"Could not open Gmail INBOX: "
                f"{mailbox_info}"
            )

        print("Gmail INBOX opened.")

        # -------------------------------------------------
        # SEARCH UNREAD EMAILS
        # -------------------------------------------------

        status, message_numbers = mail.search(
            None,
            "UNSEEN",
        )

        if status != "OK":

            raise RuntimeError(
                "Gmail UNSEEN search failed."
            )

        unread_ids = (
            message_numbers[0].split()
        )

        print(
            f"Unread email count: "
            f"{len(unread_ids)}"
        )

        if not unread_ids:

            return []

        # Get latest emails
        selected_ids = unread_ids[
            -max_emails:
        ]

        emails = []

        # -------------------------------------------------
        # FETCH EMAILS
        # -------------------------------------------------

        for message_id in selected_ids:

            print(
                f"Fetching email ID: "
                f"{message_id.decode()}"
            )

            status, message_data = mail.fetch(
                message_id,
                "(BODY.PEEK[])",
            )

            if status != "OK":

                print(
                    f"Failed to fetch "
                    f"email {message_id.decode()}"
                )

                continue

            raw_email = None

            for item in message_data:

                if (
                    isinstance(item, tuple)
                    and len(item) > 1
                    and isinstance(
                        item[1],
                        bytes,
                    )
                ):

                    raw_email = item[1]

                    break

            if raw_email is None:

                continue

            parsed_email = (
                parse_email_message(
                    raw_email
                )
            )

            parsed_email["message_id"] = (
                message_id.decode()
            )

            emails.append(
                parsed_email
            )

        print(
            f"Successfully fetched "
            f"{len(emails)} email(s)."
        )

        return emails

    except imaplib.IMAP4.error as exc:

        raise RuntimeError(
            f"Gmail IMAP error: {exc}"
        ) from exc

    finally:

        try:
            mail.logout()
        except Exception:
            pass


# =========================================================
# MARK AS READ
# =========================================================

def mark_email_as_read(
    message_id: str,
    email_address: str | None = None,
    app_password: str | None = None,
) -> None:

    email_address = (
        email_address
        or os.getenv("EMAIL_ADDRESS")
    )

    app_password = (
        app_password
        or os.getenv("APP_PASSWORD")
    )

    if not email_address:

        raise ValueError(
            "EMAIL_ADDRESS is not configured."
        )

    if not app_password:

        raise ValueError(
            "APP_PASSWORD is not configured."
        )

    mail = imaplib.IMAP4_SSL(
        "imap.gmail.com"
    )

    try:

        mail.login(
            email_address,
            app_password,
        )

        mail.select("INBOX")

        status, _ = mail.store(
            message_id,
            "+FLAGS",
            "\\Seen",
        )

        if status != "OK":

            raise RuntimeError(
                f"Failed to mark email "
                f"{message_id} as read."
            )

    finally:

        mail.logout()