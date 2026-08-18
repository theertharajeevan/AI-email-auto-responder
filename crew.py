import os

from dotenv import load_dotenv
from crewai import Agent, Crew, Task, LLM

from models import EmailClassification, EmailResponse


# ============================================================
# WORKAROUND: crewAI issue #5886
# CrewAI injects a 'cache_breakpoint' field into messages that
# only Anthropic models support. It's supposed to be stripped
# for other providers (like Groq) but that logic is currently
# broken, causing Groq to reject every request. This disables
# the cache-breakpoint tagging entirely.
# https://github.com/crewAIInc/crewAI/issues/5886
# ============================================================

import crewai.llms.cache as _crewai_cache
_crewai_cache.mark_cache_breakpoint = lambda msg: msg


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError(
        "GROQ_API_KEY is not configured in the .env file."
    )


print(
    "Using Groq API key:",
    GROQ_API_KEY[:8] + "..."
)


# ============================================================
# GROQ LLM
# ============================================================

llm = LLM(
    model="groq/openai/gpt-oss-120b",
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1",
    temperature=0.2,
)


# ============================================================
# CLASSIFICATION AGENT
# ============================================================

classification_agent = Agent(
    role="Email Classification Specialist",

    goal=(
        "Accurately classify incoming emails and determine "
        "whether they require a response."
    ),

    backstory=(
        "You are an email classification specialist. "
        "You analyze the sender's intent and classify emails "
        "consistently without inventing information."
    ),

    llm=llm,

    verbose=True,

    allow_delegation=False,
)


# ============================================================
# CLASSIFICATION TASK
# ============================================================

classification_task = Task(

    description="""
Analyze the following email.

Sender:
{sender}

Subject:
{subject}

Email Body:
{body}

Classify the email.

Available categories:

- inquiry
  General question or request for information.

- complaint
  Customer dissatisfaction or negative experience.

- support
  Technical or product-related problem.

- sales
  Purchase, pricing, quote, or commercial interest.

- spam
  Unsolicited, suspicious, or irrelevant email.

- newsletter
  Marketing, newsletter, or bulk informational email.

- other
  Anything that does not fit the above categories.

Determine:

1. category
2. whether a response is required
3. priority
4. short reason

Important rules:

- Return exactly one category.
- needs_response must be true or false.
- Priority must be low, medium, or high.
- Newsletters normally do not require a response.
- Spam normally does not require a response.
- Do not invent information.
- Focus on the sender's actual intent.
""",

    expected_output="""
Return ONLY a raw JSON object, with no markdown code fences,
no explanation, and no extra text before or after it.

The JSON object must have exactly these keys:

{
  "category": "<one of: inquiry, complaint, support, sales, spam, newsletter, other>",
  "needs_response": <true or false>,
  "priority": "<one of: low, medium, high>",
  "reason": "<short string>"
}
""",

    agent=classification_agent,
)


# ============================================================
# CLASSIFICATION CREW
# ============================================================

classification_crew = Crew(

    agents=[
        classification_agent
    ],

    tasks=[
        classification_task
    ],

    verbose=True,
)


# ============================================================
# RESPONSE WRITER AGENT
# ============================================================

response_agent = Agent(

    role="Professional Email Response Writer",

    goal=(
        "Generate a professional, concise and helpful "
        "email response based only on the provided email."
    ),

    backstory=(
        "You are an experienced professional email writer. "
        "You write polite and contextually appropriate responses "
        "without inventing information."
    ),

    llm=llm,

    verbose=True,

    allow_delegation=False,
)


# ============================================================
# RESPONSE TASK
# ============================================================

response_task = Task(

    description="""
Write a professional response to the following email.

Sender:
{sender}

Subject:
{subject}

Email Body:
{body}

Classification:
{classification}

Instructions:

- Write a professional response.
- Be polite and concise.
- Directly address the sender's request.
- Do not invent facts, dates, commitments or information.
- Do not mention that AI generated the response.
- Return only the response content.
""",

    expected_output="""
Return ONLY a raw JSON object, with no markdown code fences,
no explanation, and no extra text before or after it.

The JSON object must have exactly these keys:

{
  "subject": "<the response subject line>",
  "body": "<the response body>"
}
""",

    agent=response_agent,
)


# ============================================================
# RESPONSE CREW
# ============================================================

response_crew = Crew(

    agents=[
        response_agent
    ],

    tasks=[
        response_task
    ],

    verbose=True,
)