# Email Auto Responder

Fetches unread Gmail messages, classifies them with a CrewAI crew running
on Groq's `llama-3.3-70b-versatile`, drafts a reply, and sends it — but
only for emails that actually need a response.

## Setup

```bash
python -m venv venv
source venv/bin/activate      # venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env          # then fill in real values
```

Gmail requires an **App Password** (not your normal password) for
`APP_PASSWORD` — generate one at myaccount.google.com/apppasswords with
2-Step Verification enabled.

## Run

```bash
python main.py
```

By default `main.py` asks for confirmation (`y/N`) before sending each
reply. Set `interactive=False` in `Orchestrator(...)` once you trust the
output, or `auto_send=False` to do a dry run that drafts replies without
sending anything.

## What changed from the original version

- **`orchestrator.py` didn't exist** — `main.py` imported
  `agents.orchestrator.Orchestrator`, which was never written, so the
  program crashed immediately. This file now contains that missing piece.
- **Two competing implementations were merged into one.** The project had
  a plain LangChain/`ChatGroq` path (`classifier.py`, `response_generator.py`)
  and a separate CrewAI path (`crew.py`, `flow.py`), neither wired to
  `main.py`. Everything now runs through the CrewAI crew in `crew.py`.
- **Classification is now structured** (`models.py` + `output_pydantic`),
  so the orchestrator can gate sending on `needs_response` instead of
  writing and sending a reply to every email, including spam/newsletters.
- **The reply is now actually sent** to the original sender, using the
  parsed `From` header — previously the generated text was produced but
  never passed to `send_email()`.
- **`fetch_unread_emails` no longer marks messages as read as a side
  effect** of fetching (`BODY.PEEK[]` instead of `RFC822`). Reading is
  now marked explicitly, after an email is actually processed, and is
  skipped entirely if an error occurs — so a crash mid-run causes a
  retry next time instead of silently losing that email.
- **`requirements.txt` now lists real dependencies** (`crewai`, `litellm`,
  `pydantic`) instead of leaving them commented out.
- Removed `flow.py`, `classifier.py`, `response_generator.py`, and the
  empty `app.py` — dead/orphaned code once everything ran through one
  path. Added `.gitignore` and `.env.example` so `venv/` and real
  credentials never get committed or zipped up again.

## Security note

The `.env` in the zip you originally uploaded contained what look like
live credentials (Gmail address, Gmail app password, Groq API key).
Since that file has now been shared, treat those as compromised — revoke
the Gmail app password and regenerate the Groq API key, then put fresh
values only in your local `.env` (never in `.env.example` or in anything
you share).
