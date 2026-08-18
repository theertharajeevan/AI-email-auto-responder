# 📧 AI-Gmail auto responder

**AI-powered Gmail auto-responder with a human-in-the-loop approval workflow.**

AI-Gmail auto responder connects to your Gmail inbox, classifies unread emails using a multi-agent [CrewAI](https://www.crewai.com/) pipeline running on [Groq](https://groq.com/), drafts a professional reply when one is needed, and lets you review, edit, and approve every response before it's sent. Nothing goes out without your sign-off.

---

## ✨ Features

- **Automatic classification** — every unread email is sorted into a category (inquiry, complaint, support, sales, spam, newsletter, other), with a priority level and a short reason.
- **Smart filtering** — spam and newsletters are skipped by default; only emails that genuinely need a reply get one drafted.
- **AI-drafted responses** — a dedicated response-writing agent generates a polite, concise, context-aware reply based only on the original email (no invented facts or commitments).
- **Human-in-the-loop** — nothing is sent automatically. You review the AI's classification and draft, edit the subject/body if needed, and explicitly approve before it goes out.
- **Two ways to run it** — a Streamlit web UI for interactive review, or a CLI (`main.py`) for scripted/terminal use.
- **Safe by default** — emails are only marked as read after a response is successfully sent (or you explicitly dismiss one that needs no reply).

---

## 🏗️ How it works

```
Gmail (IMAP)
     │
     ▼
Fetch unread emails
     │
     ▼
┌─────────────────────┐
│  Classification      │  ← CrewAI agent (Groq LLM)
│  Agent                │
└─────────┬────────────┘
          │
   needs_response?
     │         │
    No        Yes
     │         │
     ▼         ▼
  Mark   ┌─────────────────────┐
  as     │  Response Writer     │  ← CrewAI agent (Groq LLM)
  read   │  Agent                │
         └─────────┬────────────┘
                    │
                    ▼
          Human review & edit
                    │
              Approve & Send?
                    │
                   Yes
                    │
                    ▼
          Gmail (SMTP) + mark as read
```

The workflow is orchestrated with a [CrewAI `Flow`](https://docs.crewai.com/concepts/flows), which chains a classification `Crew` into a response-generation `Crew`, sharing state between them.

---

## 🧰 Tech stack

- [CrewAI](https://www.crewai.com/) — multi-agent orchestration
- [Groq](https://groq.com/) — LLM inference (via `litellm`)
- [Streamlit](https://streamlit.io/) — web UI
- Python's built-in `imaplib` / `smtplib` — Gmail IMAP/SMTP access
- [Pydantic](https://docs.pydantic.dev/) — structured data validation

---

## 📋 Prerequisites

- Python 3.10+
- A Gmail account with [2-Step Verification](https://myaccount.google.com/security) enabled
- A Gmail [App Password](https://myaccount.google.com/apppasswords) (regular account passwords won't work for IMAP/SMTP)
- A [Groq API key](https://console.groq.com/keys)

---

## 🚀 Setup

**1. Clone the repository**

```bash
git clone https://github.com/<your-username>/AI-Gmail auto responder.git
cd AI-Gmail auto responder
```

**2. Create and activate a virtual environment**

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Configure environment variables**

Copy the example file and fill in your own values:

```bash
cp .env.example .env
```

```env
EMAIL_ADDRESS=your_gmail_address@gmail.com
APP_PASSWORD=your_gmail_app_password
GROQ_API_KEY=your_groq_api_key
```

> ⚠️ **Never commit your `.env` file.** It's already listed in `.gitignore` — double-check before pushing.

---

## ▶️ Usage

### Option A: Streamlit web UI (recommended)

```bash
streamlit run frontend/app.py
```

Opens an interactive dashboard where you can browse unread emails, run classification, review the AI-drafted response, edit it inline, and approve or reject sending.

### Option B: Command-line

```bash
python main.py
```

Processes unread emails one at a time in the terminal, printing the classification and draft response, and prompting `y/N` before sending each one.

---

## 📁 Project structure

```
AI-Gmail auto responder/
├── frontend/
│   └── app.py           # Streamlit UI
├── crew.py               # Agents, tasks, and crews (classification + response)
├── flow.py                # CrewAI Flow orchestrating the two crews
├── email_utils.py         # Gmail IMAP: fetch unread emails, mark as read
├── send_email.py           # Gmail SMTP: send responses
├── models.py                # Pydantic schemas (EmailClassification, EmailResponse)
├── main.py                   # CLI entry point
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🩹 Known issues & troubleshooting

- **`ImportError: ... LiteLLM fallback package is not installed`**
  Run `pip install litellm`.

- **Groq requests routed to OpenAI / `Incorrect API key provided`**
  Some `litellm` versions mis-parse nested model strings like `groq/openai/...`. Explicitly pass `base_url="https://api.groq.com/openai/v1"` when constructing the `LLM`.

- **`Tool choice is required, but model did not call a tool` / unreliable structured output**
  Certain Groq models have inconsistent forced tool-calling support. This project avoids that entirely by having agents return plain JSON (parsed manually in `flow.py`) instead of relying on `output_pydantic` tool-calling.

- **`property 'cache_breakpoint' is unsupported` (GroqException)**
  A known CrewAI bug ([crewAIInc/crewAI#5886](https://github.com/crewAIInc/crewAI/issues/5886)) injects an Anthropic-only caching field into every request, which non-Anthropic providers like Groq reject. `crew.py` includes a workaround that disables this tagging. Safe to remove once upstream fixes the issue.

- **Model not found errors**
  Groq periodically deprecates models. Check [console.groq.com/docs/models](https://console.groq.com/docs/models) for the current lineup if `crew.py`'s configured model stops working.

---

## 🔒 Privacy & safety notes

- Emails are only read to generate a classification and draft — nothing is stored or logged beyond your local terminal/Streamlit session.
- No response is ever sent without explicit human approval.
- Keep your `.env` file (Gmail app password, Groq API key) private and out of version control.

---

## 📄 License

[MIT](LICENSE) — feel free to use, modify, and adapt.

---

## 🙏 Acknowledgments

Built with [CrewAI](https://www.crewai.com/) and [Groq](https://groq.com/).
