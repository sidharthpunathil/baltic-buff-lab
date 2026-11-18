"""Data shapes shared by every step."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

BuffType = Literal["poll", "quiz", "prediction"]


class Buff(BaseModel):
    buff_type: BuffType
    title: str = Field(description="Card title, max 35 characters, target language.")
    question: str = Field(description="The question shown to fans, in the target language.")
    options: list[str] = Field(description="2-4 short answer options, in the target language.")
    correct_index: int | None = Field(
        default=None, description="Index of the correct option for quiz buffs, else null."
    )
    reveal: str = Field(
        description="One short sentence shown after the buff closes (fact or result), target language."
    )
    english_gloss: str = Field(
        description="Literal English back-gloss of question + options so a non-native operator can approve it."
    )


class BuffDraft(BaseModel):
    """What the generator returns: the buff plus its self-check."""

    reasoning_notes: str = Field(
        description="2-4 short notes on case/agreement choices made (e.g. which case a name takes and why)."
    )
    buff: Buff


class EnglishBuff(BaseModel):
    buff: Buff


class CaseForm(BaseModel):
    case: str
    singular: str = Field(description="Full name (or full team name) in this case.")
    short: str = Field(description="Short form used in running sports copy in this case: surname only for players, short club name for teams.")


class EntityForms(BaseModel):
    lemma: str = Field(description="Nominative form used in this language's sports media.")
    gender: Literal["masculine", "feminine", "none", "plural"]
    declines: bool = Field(description="Whether this name takes case endings in running text.")
    forms: list[CaseForm]
    usage_note: str


class MQMError(BaseModel):
    category: Literal[
        "grammar-case",
        "grammar-agreement",
        "grammar-other",
        "spelling-diacritics",
        "terminology",
        "name-form",
        "fluency-translationese",
        "accuracy-facts",
        "style-register",
        "ui-fit",
    ]
    severity: Literal["minor", "major", "critical"]
    span: str
    explanation: str
    suggested_fix: str


class Judgement(BaseModel):
    errors: list[MQMError]
    grammar: int = Field(ge=1, le=5)
    naturalness: int = Field(ge=1, le=5)
    terminology: int = Field(ge=1, le=5)
    faithfulness: int = Field(ge=1, le=5)
    engagement: int = Field(ge=1, le=5)
    verdict: Literal["approve", "revise", "reject"]
    native_rewrite: Buff | None = Field(
        default=None, description="A corrected version if verdict is not approve, else null."
    )

    @property
    def mqm_penalty(self) -> int:
        weights = {"minor": 1, "major": 5, "critical": 10}
        return sum(weights[e.severity] for e in self.errors)

    @property
    def mean_score(self) -> float:
        return round(
            (self.grammar + self.naturalness + self.terminology + self.faithfulness + self.engagement) / 5, 2
        )
