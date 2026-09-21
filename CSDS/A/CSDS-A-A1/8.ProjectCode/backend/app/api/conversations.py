"""F3 chat: conversations about one policy, each answer cited and scored for faithfulness."""

from __future__ import annotations

from fastapi import APIRouter, status
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbSession, get_owned_policy
from app.core.config import get_settings
from app.core.db import utcnow
from app.core.errors import AppError, NotFound
from app.models import Conversation, Message, Policy
from app.schemas.chat import (
    ConversationCreate,
    ConversationDetail,
    ConversationOut,
    ExchangeOut,
    MessageIn,
    MessageOut,
)

router = APIRouter(prefix="/conversations", tags=["chat"])


def _owned(db, user, conversation_id: int) -> Conversation:  # noqa: ANN001
    conv = db.get(Conversation, conversation_id)
    if conv is None or conv.user_id != user.id:
        raise NotFound("Conversation not found.")
    return conv


def _out(db, conv: Conversation) -> ConversationOut:  # noqa: ANN001
    policy = db.get(Policy, conv.policy_id)
    count = db.scalar(select(func.count()).select_from(Message).where(Message.conversation_id == conv.id)) or 0
    return ConversationOut(id=conv.id, policy_id=conv.policy_id, policy_name=policy.display_name if policy else "",
                           title=conv.title, created_at=conv.created_at, updated_at=conv.updated_at,
                           message_count=count)


@router.get("", response_model=list[ConversationOut])
def list_conversations(user: CurrentUser, db: DbSession, policy_id: int | None = None) -> list[ConversationOut]:
    q = select(Conversation).where(Conversation.user_id == user.id)
    if policy_id is not None:
        q = q.where(Conversation.policy_id == policy_id)
    return [_out(db, c) for c in db.scalars(q.order_by(Conversation.updated_at.desc())).all()]


@router.post("", response_model=ConversationOut, status_code=status.HTTP_201_CREATED)
def create_conversation(body: ConversationCreate, user: CurrentUser, db: DbSession) -> ConversationOut:
    policy = get_owned_policy(db, user, body.policy_id)
    conv = Conversation(user_id=user.id, policy_id=policy.id, title=(body.title or "New conversation")[:200])
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return _out(db, conv)


@router.get("/{conversation_id}", response_model=ConversationDetail)
def get_conversation(conversation_id: int, user: CurrentUser, db: DbSession) -> ConversationDetail:
    conv = _owned(db, user, conversation_id)
    base = _out(db, conv)
    return ConversationDetail(**base.model_dump(), messages=[MessageOut.model_validate(m) for m in conv.messages])


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(conversation_id: int, user: CurrentUser, db: DbSession) -> None:
    conv = _owned(db, user, conversation_id)
    db.delete(conv)
    db.commit()


@router.post("/{conversation_id}/messages", response_model=ExchangeOut)
def ask(conversation_id: int, body: MessageIn, user: CurrentUser, db: DbSession) -> ExchangeOut:
    from app.services.answerer import answer_question

    conv = _owned(db, user, conversation_id)
    policy = get_owned_policy(db, user, conv.policy_id)
    if policy.document.status not in ("ready", "extracting"):
        raise AppError("This policy is still being processed. Please wait until it is ready.", code="busy",
                       status_code=409)
    language = body.language or user.language or "en"
    if language not in get_settings().supported_languages:
        language = "en"
    history = [(m.role, m.content_en or m.content) for m in conv.messages[-6:]]
    question = body.question.strip()

    result = answer_question(policy.document_id, question, language, history, user.id)

    user_msg = Message(conversation_id=conv.id, role="user", content=question, language=language)
    answer_msg = Message(
        conversation_id=conv.id, role="assistant", content=result.answer, content_en=result.answer_en,
        language=language, status=result.status, citations=result.citations,
        faithfulness=result.faithfulness.get("score"), faithfulness_detail=result.faithfulness,
        retrieval=result.retrieval | {"follow_ups": result.follow_ups}, timings=result.timings,
        total_ms=result.timings.get("total_ms"), model=result.model,
    )
    db.add_all([user_msg, answer_msg])
    if conv.title == "New conversation" or not conv.messages:
        conv.title = question[:80] + ("…" if len(question) > 80 else "")
    conv.updated_at = utcnow()
    db.commit()
    db.refresh(user_msg)
    db.refresh(answer_msg)
    return ExchangeOut(question=MessageOut.model_validate(user_msg), answer=MessageOut.model_validate(answer_msg),
                       follow_ups=result.follow_ups)
