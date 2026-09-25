from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    token: str
    email: str
    user_id: int


class FlagResponse(BaseModel):
    id: int
    rule_id: str
    rule_label: str
    severity: str
    reason: str
    provision: str
    safer_wording: str

    class Config:
        from_attributes = True


class ClauseResponse(BaseModel):
    id: int
    index_in_doc: int
    page_number: int
    text: str
    clause_type: str
    classification_confidence: float
    classification_method: str
    flags: list[FlagResponse] = []

    class Config:
        from_attributes = True


class ClauseSummary(BaseModel):
    id: int
    index_in_doc: int
    page_number: int
    clause_type: str
    text_preview: str
    flag_count: int
    max_severity: str


class ContractSummaryResponse(BaseModel):
    id: int
    filename: str
    uploaded_at: str
    complexity_grade: str
    complexity_score: float
    flag_count: int


class ContractReportResponse(BaseModel):
    id: int
    filename: str
    uploaded_at: str
    complexity_grade: str
    complexity_score: float
    readability_score: float
    legalese_density: float
    cross_reference_count: int
    avg_sentence_length: float
    plain_summary: str
    key_obligations: list[str]
    combo_flags: list[dict]
    clauses: list[ClauseSummary]
