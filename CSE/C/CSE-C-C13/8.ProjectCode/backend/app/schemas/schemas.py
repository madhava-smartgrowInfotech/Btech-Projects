"""Pydantic request/response schemas."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


# ---------- Auth / users ----------

class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    public_key: str = Field(min_length=10, description="Base64 SPKI RSA-2048 public key")
    encrypted_private_key: str = Field(min_length=10, description="JSON bundle of encrypted private key")
    private_key_salt: str = Field(min_length=8)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: str
    public_key: str | None = None
    has_private_key: bool = False
    is_active: bool = True
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class UpdateKeysRequest(BaseModel):
    public_key: str
    encrypted_private_key: str
    private_key_salt: str


# ---------- Files ----------

class FileOut(BaseModel):
    id: int
    original_filename: str
    mime_type: str
    encrypted_size: int
    original_size: int
    owner_id: int
    owner_name: str | None = None
    owner_email: str | None = None
    effective_role: str = "owner"
    plaintext_sha256: str
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class FileDetailOut(FileOut):
    iv: str
    wrapped_fek: str
    stored_filename: str | None = None


class PermissionOut(BaseModel):
    user_id: int
    user_name: str | None = None
    user_email: str | None = None
    role: str
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class ShareRequest(BaseModel):
    user_id: int | None = None
    email: EmailStr | None = None
    role: str = Field(pattern="^(viewer|editor)$")
    wrapped_fek: str = Field(min_length=10)


class ChangeRoleRequest(BaseModel):
    role: str = Field(pattern="^(viewer|editor)$")


# ---------- Audit ----------

class AuditOut(BaseModel):
    id: int
    timestamp_utc: datetime | None = None
    user_id: int | None = None
    user_email: str | None = None
    file_id: int | None = None
    action: str
    success: bool
    ip_address: str | None = None
    details: str = ""
    previous_hash: str
    current_hash: str

    model_config = {"from_attributes": True}


class AuditVerifyOut(BaseModel):
    valid: bool
    checked: int
    failure_at: int | None = None
    message: str
