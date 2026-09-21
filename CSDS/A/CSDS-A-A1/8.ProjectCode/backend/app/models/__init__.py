"""SQLAlchemy models. Importing this package registers every table."""

from app.models.chat import Conversation, Message
from app.models.claim import ClaimCase
from app.models.comparison import Comparison
from app.models.document import Clause, Document, PolicyCard, RiskFlag
from app.models.llm_call import LlmCall
from app.models.policy import Policy
from app.models.translation import Translation
from app.models.user import User

__all__ = [
    "ClaimCase",
    "Clause",
    "Comparison",
    "Conversation",
    "Document",
    "LlmCall",
    "Message",
    "Policy",
    "PolicyCard",
    "RiskFlag",
    "Translation",
    "User",
]
