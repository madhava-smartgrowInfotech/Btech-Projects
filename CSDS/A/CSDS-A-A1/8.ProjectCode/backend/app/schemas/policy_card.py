"""JSON schema for schema-constrained Policy Card extraction (sent to Gemini as ``response_schema``)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

PROMPT_VERSION = "card-v4"


class Sourced(BaseModel):
    value: str = Field(description="The value in plain words exactly as the policy states it, e.g. 'Rs. 5 lakh to "
                                   "Rs. 1 crore', '24 months', '20% of admissible claim'. Use 'Not specified in "
                                   "this policy' when the text does not state it.")
    number: float | None = Field(default=None, description="Main number, normalised: rupees for amounts (1 lakh = "
                                 "100000, 1 crore = 10000000), percent for percentages, months for waiting periods "
                                 "(2 years = 24), days for day counts, hours for hour limits.")
    unit: Literal["INR", "percent", "months", "days", "hours", "times", "none"] = "none"
    clause: str | None = Field(default=None, description="Tag of the clause that states it, e.g. 'C42'.")
    quote: str | None = Field(default=None, description="Short quote (max 30 words) copied character-for-character "
                                                        "from that clause.")
    found: bool = Field(description="False when the policy text does not state this item.")


class NamedSourced(Sourced):
    name: str = Field(description="Short name, e.g. 'Cataract', 'Age 61 and above', 'Zone B hospitals'.")


class WaitingPeriods(BaseModel):
    initial: Sourced = Field(description="Initial waiting period for illnesses (usually 30 days).")
    pre_existing: Sourced = Field(description="Waiting period for pre-existing diseases.")
    specific_diseases: Sourced = Field(description="Waiting period for the listed specific diseases/procedures.")
    maternity: Sourced = Field(description="Waiting period for maternity benefits, if any.")


class ClaimTimelines(BaseModel):
    planned_intimation: Sourced = Field(description="How early to inform the insurer before planned hospitalisation.")
    emergency_intimation: Sourced = Field(description="Deadline to inform the insurer after an emergency admission.")
    reimbursement_documents: Sourced = Field(description="Deadline to submit reimbursement claim documents.")


class CardSummary(BaseModel):
    overview: str = Field(description="2-3 plain-language sentences: what this policy is and its main strengths.")
    best_for: list[str] = Field(description="Up to 3 kinds of buyers this policy suits.")
    watch_outs: list[str] = Field(description="Up to 5 cost or coverage traps a policyholder should know.")
    next_actions: list[str] = Field(description="Up to 4 concrete next steps for the policyholder.")


class AiRisk(BaseModel):
    title: str = Field(description="Short title of the gotcha, e.g. 'Cataract capped at Rs. 40,000 per eye'.")
    severity: Literal["high", "medium", "low"]
    category: Literal["waiting_period", "sub_limit", "co_payment", "room_rent", "deductible", "exclusion",
                      "claim_process", "other"]
    explanation: str = Field(description="One or two sentences on why it matters, in plain language.")
    clause: str | None = Field(default=None, description="Clause tag, e.g. 'C42'.")
    quote: str | None = Field(default=None, description="Short verbatim quote from that clause.")


class PolicyCardExtraction(BaseModel):
    insurer: str
    product_name: str
    uin: str | None = Field(default=None, description="IRDAI Unique Identification Number of the product.")
    policy_type: str = Field(description="Individual, Family floater, or both.")
    sum_insured: Sourced
    deductible: Sourced
    co_payment: Sourced = Field(description="General co-payment on every claim, if any.")
    co_payment_conditions: list[NamedSourced] = Field(description="Conditional co-payments (age, zone, network, "
                                                                  "optional covers). Empty list if none.")
    room_rent_limit: Sourced
    icu_limit: Sourced
    waiting_periods: WaitingPeriods
    specific_disease_examples: list[str] = Field(description="Up to 12 conditions named in the specific-disease "
                                                             "waiting period list, e.g. cataract, joint replacement.")
    sub_limits: list[NamedSourced] = Field(description="Caps on particular treatments or expenses. Empty if none.")
    pre_hospitalization: Sourced
    post_hospitalization: Sourced
    day_care: Sourced
    ambulance: Sourced
    restoration: Sourced = Field(description="Restoration / recharge / reload of the sum insured.")
    cumulative_bonus: Sourced = Field(description="No-claim / cumulative bonus.")
    ayush: Sourced
    modern_treatments: Sourced
    maternity_cover: Sourced
    key_exclusions: list[NamedSourced] = Field(description="The 6-10 exclusions most likely to affect a claim.")
    claim_timelines: ClaimTimelines
    free_look_period: Sourced
    grace_period: Sourced
    moratorium_period: Sourced
    summary: CardSummary
    ai_risks: list[AiRisk] = Field(description="3-8 gotchas: long waiting periods, sub-limits, co-pay traps, "
                                               "room-rent linked deductions, strict claim deadlines.")


# Field groups shown on the Policy Card, in order (key, label).
CARD_FIELDS: list[tuple[str, str]] = [
    ("sum_insured", "Sum insured"),
    ("deductible", "Deductible"),
    ("co_payment", "Co-payment"),
    ("room_rent_limit", "Room rent"),
    ("icu_limit", "ICU"),
    ("pre_hospitalization", "Pre-hospitalisation"),
    ("post_hospitalization", "Post-hospitalisation"),
    ("day_care", "Day-care procedures"),
    ("ambulance", "Ambulance"),
    ("restoration", "Restoration of sum insured"),
    ("cumulative_bonus", "No-claim bonus"),
    ("ayush", "AYUSH treatment"),
    ("modern_treatments", "Modern treatments"),
    ("maternity_cover", "Maternity"),
    ("free_look_period", "Free-look period"),
    ("grace_period", "Grace period"),
    ("moratorium_period", "Moratorium period"),
]

WAITING_FIELDS: list[tuple[str, str]] = [
    ("initial", "Initial waiting period"),
    ("pre_existing", "Pre-existing diseases"),
    ("specific_diseases", "Specific diseases / procedures"),
    ("maternity", "Maternity"),
]

TIMELINE_FIELDS: list[tuple[str, str]] = [
    ("planned_intimation", "Planned hospitalisation - inform insurer"),
    ("emergency_intimation", "Emergency admission - inform insurer"),
    ("reimbursement_documents", "Reimbursement - submit documents"),
]
