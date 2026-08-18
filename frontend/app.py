import sys
from pathlib import Path


import streamlit as st


# =========================================================
# PROJECT ROOT
# =========================================================

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

if str(PROJECT_ROOT) not in sys.path:

    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )


# =========================================================
# BACKEND IMPORTS
# =========================================================

from email_utils import (
    fetch_unread_emails,
    mark_email_as_read,
)

from flow import EmailResponderFlow

from send_email import send_email


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="AI Email Auto Responder",
    page_icon="📧",
    layout="wide",
)


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 32px;
        font-weight: 700;
        margin-bottom: 5px;
    }

    .subtitle {
        color: #6b7280;
        font-size: 16px;
        margin-bottom: 25px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# SESSION STATE
# =========================================================

defaults = {
    "emails": [],
    "selected_email": None,
    "classification": None,
    "response": None,
    "emails_loaded": False,
}



for key, value in defaults.items():

    if key not in st.session_state:

        st.session_state[key] = value

# =========================================================
# INITIAL EMAIL LOAD
# =========================================================

if not st.session_state.emails_loaded:

    try:

        with st.spinner(
            "Connecting to Gmail and fetching unread emails..."
        ):

            st.session_state.emails = (
                fetch_unread_emails()
            )

        st.session_state.emails_loaded = True

    except Exception as exc:

        st.session_state.emails_loaded = True

        st.error(
            f"Failed to load Gmail emails:\n\n"
            f"{type(exc).__name__}: {exc}"
        )


# =========================================================
# HEADER
# =========================================================

st.markdown(
    """
    <div class="main-title">
        📧 AI Email Auto Responder
    </div>

    <div class="subtitle">
        Gmail + CrewAI + Human-in-the-Loop
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:

    st.header("📬 Inbox")

    if st.button(
        "🔄 Refresh Emails",
        use_container_width=True,
    ):

        try:

            with st.spinner(
                "Fetching unread emails..."
            ):

                emails = fetch_unread_emails()

            st.session_state.emails = emails

            st.session_state.selected_email = None

            st.session_state.classification = None

            st.session_state.response = None

            st.session_state.emails_loaded = True

            st.success(
                f"Found {len(emails)} "
                f"unread email(s)."
            )

            st.rerun()

        except Exception as exc:

            st.error(
                f"Failed to fetch emails:\n\n"
                f"{type(exc).__name__}: {exc}"
            )

    st.divider()

    st.metric(
        "Unread Emails",
        len(st.session_state.emails),
    )


# =========================================================
# NO EMAILS
# =========================================================

if not st.session_state.emails:

    st.info(
        "📭 No unread emails found in Gmail."
    )
    st.stop()


# =========================================================
# MAIN LAYOUT
# =========================================================

email_column, details_column = (
    st.columns(
        [1, 2],
        gap="large",
    )
)


# =========================================================
# EMAIL LIST
# =========================================================

with email_column:

    st.subheader("📥 Unread Emails")

    for index, email_data in enumerate(
        st.session_state.emails
    ):

        sender = email_data.get(
            "sender",
            "Unknown sender",
        )

        subject = email_data.get(
            "subject",
            "(No subject)",
        )

        if len(sender) > 30:

            sender = sender[:30] + "..."

        if len(subject) > 40:

            subject = subject[:40] + "..."

        if st.button(
            f"{sender}\n\n{subject}",
            key=f"email_{index}",
            use_container_width=True,
        ):

            st.session_state.selected_email = (
                index
            )

            st.session_state.classification = None

            st.session_state.response = None

            st.rerun()


# =========================================================
# SELECTED EMAIL
# =========================================================

selected_index = (
    st.session_state.selected_email
)

if selected_index is None:

    with details_column:

        st.info(
            "Select an email from the left."
        )

    st.stop()


email_data = st.session_state.emails[
    selected_index
]


# =========================================================
# EMAIL DETAILS
# =========================================================

with details_column:

    st.subheader("✉️ Email")

    st.write(
        f"**From:** "
        f"{email_data.get('sender', '')}"
    )

    st.write(
        f"**Subject:** "
        f"{email_data.get('subject', '')}"
    )

    st.divider()

    st.write("### Email Body")

    st.text_area(
        "Email body",
        value=email_data.get(
            "body",
            "",
        ),
        height=300,
        disabled=True,
        label_visibility="collapsed",
    )

    st.divider()


    # =====================================================
    # ANALYZE
    # =====================================================

    if (
        st.session_state.classification
        is None
    ):

        if st.button(
            "🤖 Analyze Email",
            type="primary",
            use_container_width=True,
        ):

            try:

                with st.spinner(
                    "CrewAI is analyzing "
                    "the email..."
                ):

                    flow = (
                        EmailResponderFlow()
                    )

                    flow.kickoff(
                        inputs={
                            "sender": email_data[
                                "sender"
                            ],

                            "subject": email_data[
                                "subject"
                            ],

                            "body": email_data[
                                "body"
                            ],
                        }
                    )

                st.session_state.classification = (
                    flow.state[
                        "classification"
                    ]
                )

                st.session_state.response = (
                    flow.state.get(
                        "response"
                    )
                )

                st.rerun()

            except Exception as exc:

                st.error(
                    f"Analysis failed:\n\n"
                    f"{type(exc).__name__}: {exc}"
                )


# =========================================================
# CLASSIFICATION
# =========================================================

classification = (
    st.session_state.classification
)

if classification is None:

    st.stop()


st.subheader(
    "🤖 AI Classification"
)


col1, col2, col3 = st.columns(3)


with col1:

    st.metric(
        "Category",
        classification.category,
    )


with col2:

    st.metric(
        "Priority",
        classification.priority,
    )


with col3:

    st.metric(
        "Needs Response",
        (
            "Yes"
            if classification.needs_response
            else "No"
        ),
    )


st.info(
    f"**Reason:** "
    f"{classification.reason}"
)


# =========================================================
# NO RESPONSE REQUIRED
# =========================================================

if not classification.needs_response:

    st.success(
        "This email does not require "
        "a response."
    )

    if st.button(
        "✓ Mark as Read",
        type="primary",
        use_container_width=True,
    ):

        try:

            mark_email_as_read(
                email_data[
                    "message_id"
                ]
            )

            st.success(
                "Email marked as read."
            )

            st.session_state.emails.pop(
                selected_index
            )

            st.session_state.selected_email = (
                None
            )

            st.session_state.classification = (
                None
            )

            st.session_state.response = None

            st.rerun()

        except Exception as exc:

            st.error(
                f"Failed to mark email as read:\n\n"
                f"{type(exc).__name__}: {exc}"
            )

    st.stop()


# =========================================================
# RESPONSE
# =========================================================

st.subheader(
    "✍️ Generated Response"
)

response = (
    st.session_state.response
)

if response is None:

    st.warning(
        "The email requires a response, "
        "but no response was generated."
    )

    st.stop()


# =========================================================
# HUMAN EDITING
# =========================================================

response_subject = st.text_input(
    "Response Subject",
    value=response.subject,
)

response_body = st.text_area(
    "Response Body",
    value=response.body,
    height=250,
)


st.caption(
    "You can edit the AI-generated response "
    "before sending it."
)


# =========================================================
# HUMAN APPROVAL
# =========================================================

st.subheader(
    "👤 Human Approval"
)


approve_column, reject_column = (
    st.columns(2)
)


# =========================================================
# APPROVE & SEND
# =========================================================

with approve_column:

    if st.button(
        "✅ Approve & Send",
        type="primary",
        use_container_width=True,
    ):

        recipient = (
            email_data.get(
                "reply_to_email"
            )
            or email_data.get(
                "sender_email"
            )
        )

        if not recipient:

            st.error(
                "Could not determine "
                "the recipient email."
            )

        else:

            try:

                with st.spinner(
                    "Sending response..."
                ):

                    send_email(
                        recipient=recipient,
                        subject=response_subject,
                        body=response_body,
                    )

                    # Mark original email as read
                    # ONLY after successful send
                    mark_email_as_read(
                        email_data[
                            "message_id"
                        ]
                    )

                st.success(
                    "Response sent successfully "
                    "and email marked as read."
                )

                st.session_state.emails.pop(
                    selected_index
                )

                st.session_state.selected_email = (
                    None
                )

                st.session_state.classification = (
                    None
                )

                st.session_state.response = None

                st.rerun()

            except Exception as exc:

                st.error(
                    f"Failed to send response:\n\n"
                    f"{type(exc).__name__}: {exc}"
                )


# =========================================================
# REJECT
# =========================================================

with reject_column:

    if st.button(
        "❌ Reject Response",
        use_container_width=True,
    ):

        st.warning(
            "Response rejected. "
            "The email will remain unread."
        )

        st.session_state.response = None

        st.session_state.classification = None

        st.rerun()