import json
import re

from crewai.flow.flow import (
    Flow,
    start,
    listen,
)

from crew import (
    classification_crew,
    response_crew,
)

from models import (
    EmailClassification,
    EmailResponse,
)


def _extract_json(raw_text: str) -> dict:
    """
    Extracts a JSON object from raw LLM text output, tolerating
    markdown code fences or stray text before/after the JSON.
    """

    text = raw_text.strip()

    # Strip ```json ... ``` or ``` ... ``` fences if present
    fence_match = re.search(
        r"```(?:json)?\s*(\{.*\})\s*```",
        text,
        re.DOTALL,
    )

    if fence_match:
        text = fence_match.group(1)

    else:
        # Fall back to grabbing the first {...} block found
        brace_match = re.search(r"\{.*\}", text, re.DOTALL)

        if brace_match:
            text = brace_match.group(0)

    return json.loads(text)


class EmailResponderFlow(Flow):
    """
    Orchestrates the email auto-responder workflow.

    Email
        ↓
    Classification
        ↓
    needs_response?
        ├── False → stop
        └── True → generate response
    """

    # =====================================================
    # CLASSIFICATION
    # =====================================================

    @start()
    def classify_email(self):

        sender = self.state["sender"]
        subject = self.state["subject"]
        body = self.state["body"][:5000]

        print("\nRunning email classification...")

        result = classification_crew.kickoff(
            inputs={
                "sender": sender,
                "subject": subject,
                "body": body,
            }
        )

        try:

            classification_data = _extract_json(
                result.raw
            )

            classification = EmailClassification(
                **classification_data
            )

        except Exception as exc:

            raise ValueError(
                "Classification did not return "
                f"valid EmailClassification JSON: {exc}\n"
                f"Raw output: {result.raw}"
            ) from exc

        self.state["classification"] = classification

        print("\nClassification result:")

        print(
            classification.model_dump_json(
                indent=2
            )
        )

        return classification

    # =====================================================
    # RESPONSE GENERATION
    # =====================================================

    @listen(classify_email)
    def generate_response(
        self,
        classification: EmailClassification,
    ):

        # -------------------------------------------------
        # No response required
        # -------------------------------------------------

        if not classification.needs_response:

            print(
                "\nEmail does not require "
                "a response."
            )

            self.state["response"] = None

            return None

        # -------------------------------------------------
        # Response required
        # -------------------------------------------------

        print(
            "\nEmail requires a response."
        )

        print(
            "Generating response..."
        )

        sender = self.state["sender"]

        subject = self.state["subject"]

        body = self.state["body"][:5000]

        result = response_crew.kickoff(
            inputs={
                "sender": sender,
                "subject": subject,
                "body": body,
                "classification": (
                    classification.model_dump()
                ),
            }
        )

        try:

            response_data = _extract_json(
                result.raw
            )

            response = EmailResponse(
                **response_data
            )

        except Exception as exc:

            raise ValueError(
                "Response writer did not return "
                f"valid EmailResponse JSON: {exc}\n"
                f"Raw output: {result.raw}"
            ) from exc

        self.state["response"] = response

        print(
            "\nResponse generated successfully."
        )

        return response