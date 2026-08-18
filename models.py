from typing import Literal

from pydantic import BaseModel, Field


class EmailClassification(BaseModel):
    """
    Structured result returned by the email classification agent.
    """

    category: Literal[
        "inquiry",
        "complaint",
        "support",
        "sales",
        "spam",
        "newsletter",
        "other",
    ] = Field(
        description="The category of the email."
    )

    needs_response: bool = Field(
        description="Whether the email requires a human response."
    )

    priority: Literal[
        "low",
        "medium",
        "high",
    ] = Field(
        description="The priority of the email."
    )

    reason: str = Field(
        description="Short explanation for the classification."
    )


class EmailResponse(BaseModel):
    """
    Structured result returned by the response writer agent.
    """

    subject: str = Field(
        description="The subject line for the response email."
    )

    body: str = Field(
        description="The email response body."
    )