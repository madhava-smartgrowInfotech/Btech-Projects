import enum
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, Boolean, Text, Float, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    VOTER = "VOTER"
    AUDITOR = "AUDITOR"

class ElectionStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    OPEN = "OPEN"
    PAUSED = "PAUSED"
    CLOSED = "CLOSED"

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    display_name: Mapped[str] = mapped_column(String(128), nullable=False)
    email: Mapped[str] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    voter_profile = relationship("VoterProfile", back_populates="user", uselist=False)

class VoterProfile(Base):
    __tablename__ = "voter_profiles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(128), nullable=False)
    aadhaar_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    aadhaar_masked: Mapped[str] = mapped_column(String(32), nullable=False)
    dob: Mapped[str] = mapped_column(String(32), nullable=True)
    address: Mapped[str] = mapped_column(String(256), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    user = relationship("User", back_populates="voter_profile")

class Election(Base):
    __tablename__ = "elections"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[str] = mapped_column(String(16), default=ElectionStatus.DRAFT.value)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    candidates = relationship("Candidate", back_populates="election", cascade="all, delete-orphan")

class Candidate(Base):
    __tablename__ = "candidates"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    election_id: Mapped[int] = mapped_column(ForeignKey("elections.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    party: Mapped[str] = mapped_column(String(128), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    manifesto: Mapped[str] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    election = relationship("Election", back_populates="candidates")

class VoterEligibility(Base):
    __tablename__ = "voter_eligibility"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    election_id: Mapped[int] = mapped_column(ForeignKey("elections.id", ondelete="CASCADE"), nullable=False)
    voter_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    is_eligible: Mapped[bool] = mapped_column(Boolean, default=True)
    __table_args__ = (UniqueConstraint("election_id", "voter_user_id", name="uq_eligibility"),)

class VotingAuthorization(Base):
    __tablename__ = "voting_authorizations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    election_id: Mapped[int] = mapped_column(ForeignKey("elections.id", ondelete="CASCADE"), nullable=False)
    voter_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("election_id", "voter_user_id", name="uq_auth_one_per_election"),)

class Ballot(Base):
    __tablename__ = "ballots"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    election_id: Mapped[int] = mapped_column(ForeignKey("elections.id", ondelete="CASCADE"), nullable=False)
    ballot_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    encrypted_choice: Mapped[str] = mapped_column(Text, nullable=False)
    nonce: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    tx_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    block_index: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    # no voter identity here - separation

class VoterParticipation(Base):
    __tablename__ = "voter_participation"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    election_id: Mapped[int] = mapped_column(ForeignKey("elections.id", ondelete="CASCADE"), nullable=False)
    voter_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    ballot_id: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("election_id", "voter_user_id", name="uq_one_vote_per_voter"),)

class LedgerBlock(Base):
    __tablename__ = "ledger_blocks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    block_index: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    previous_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    merkle_root: Mapped[str] = mapped_column(String(128), nullable=False)
    block_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    validator_signatures: Mapped[str] = mapped_column(Text, nullable=False)  # JSON
    transaction_count: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class LedgerTransaction(Base):
    __tablename__ = "ledger_transactions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tx_hash: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    block_index: Mapped[int] = mapped_column(ForeignKey("ledger_blocks.block_index"), nullable=False)
    election_id: Mapped[int] = mapped_column(ForeignKey("elections.id"), nullable=False)
    ballot_id: Mapped[str] = mapped_column(String(64), nullable=False)
    encrypted_payload: Mapped[str] = mapped_column(Text, nullable=False)
    nonce: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    signature: Mapped[str] = mapped_column(Text, nullable=False)
    __table_args__ = (Index("ix_tx_election", "election_id"),)

class ValidatorNode(Base):
    __tablename__ = "validator_nodes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    node_id: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    public_key: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    actor_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    actor_username: Mapped[str] = mapped_column(String(64), nullable=True)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=True)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=True)
    details: Mapped[str] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str] = mapped_column(String(64), nullable=True)

class BenchmarkRun(Base):
    __tablename__ = "benchmark_runs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    total_ops: Mapped[int] = mapped_column(Integer, nullable=False)
    sync_duration: Mapped[float] = mapped_column(Float, nullable=False)
    async_duration: Mapped[float] = mapped_column(Float, nullable=True)
    throughput_sync: Mapped[float] = mapped_column(Float, nullable=True)
    throughput_async: Mapped[float] = mapped_column(Float, nullable=True)
    mean_latency_ms: Mapped[float] = mapped_column(Float, nullable=True)
    p95_latency_ms: Mapped[float] = mapped_column(Float, nullable=True)
    details_json: Mapped[str] = mapped_column(Text, nullable=True)
