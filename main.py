from email_utils import (
    fetch_unread_emails,
    mark_email_as_read,
)

from flow import EmailResponderFlow

from send_email import send_email


def process_email(
    email_data: dict,
) -> None:

    print("\n" + "=" * 70)

    print(
        f"From: {email_data['sender']}"
    )

    print(
        f"Subject: {email_data['subject']}"
    )

    print("=" * 70)

    # -----------------------------------------------------
    # CrewAI
    # -----------------------------------------------------

    flow = EmailResponderFlow()

    flow.kickoff(
        inputs={
            "sender": email_data["sender"],
            "subject": email_data["subject"],
            "body": email_data["body"],
        }
    )

    classification = (
        flow.state["classification"]
    )

    response = (
        flow.state.get("response")
    )

    # -----------------------------------------------------
    # Classification
    # -----------------------------------------------------

    print("\nClassification:")

    print(
        classification.model_dump_json(
            indent=2
        )
    )

    # -----------------------------------------------------
    # No response
    # -----------------------------------------------------

    if not classification.needs_response:

        print(
            "\nNo response required."
        )

        mark_email_as_read(
            email_data["message_id"]
        )

        print(
            "Email marked as read."
        )

        return

    # -----------------------------------------------------
    # Response
    # -----------------------------------------------------

    if response is None:

        print(
            "\nNo response was generated."
        )

        print(
            "Email remains unread."
        )

        return

    print(
        "\nGenerated Response:"
    )

    print(
        f"\nSubject: {response.subject}"
    )

    print(
        f"\n{response.body}"
    )

    # -----------------------------------------------------
    # Human approval
    # -----------------------------------------------------

    approval = input(
        "\nSend this response? [y/N]: "
    ).strip().lower()

    if approval != "y":

        print(
            "\nResponse rejected."
        )

        print(
            "Email remains unread."
        )

        return

    # -----------------------------------------------------
    # Recipient
    # -----------------------------------------------------

    recipient = (
        email_data.get(
            "reply_to_email"
        )
        or email_data.get(
            "sender_email"
        )
    )

    if not recipient:

        print(
            "\nCould not determine recipient."
        )

        return

    # -----------------------------------------------------
    # Send
    # -----------------------------------------------------

    try:

        send_email(
            recipient=recipient,
            subject=response.subject,
            body=response.body,
        )

        print(
            "\nResponse sent successfully."
        )

    except Exception as exc:

        print(
            f"\nFailed to send response: "
            f"{exc}"
        )

        return

    # -----------------------------------------------------
    # Mark read
    # -----------------------------------------------------

    mark_email_as_read(
        email_data["message_id"]
    )

    print(
        "Original email marked as read."
    )


def main():

    print(
        "\n📧 AI Email Auto Responder"
    )

    print(
        "Checking unread emails..."
    )

    try:

        emails = (
            fetch_unread_emails()
        )

    except Exception as exc:

        print(
            f"\nFailed to fetch emails: "
            f"{exc}"
        )

        return

    if not emails:

        print(
            "\nNo unread emails."
        )

        return

    print(
        f"\nFound {len(emails)} "
        f"unread email(s)."
    )

    for email_data in emails:

        try:

            process_email(
                email_data
            )

        except Exception as exc:

            print(
                f"\nError processing email: "
                f"{exc}"
            )

            print(
                "Email remains unread."
            )


if __name__ == "__main__":
    main()