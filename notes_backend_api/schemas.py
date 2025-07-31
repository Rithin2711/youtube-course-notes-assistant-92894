from typing import Optional, List, Literal
from pydantic import BaseModel, EmailStr, Field

# --- User ---

# PUBLIC_INTERFACE
class UserCreate(BaseModel):
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., min_length=6, description="User password")

# PUBLIC_INTERFACE
class UserLogin(BaseModel):
    email: EmailStr
    password: str

# PUBLIC_INTERFACE
class UserOut(BaseModel):
    id: int
    email: EmailStr
    class Config:
        orm_mode = True

# --- Auth token ---

# PUBLIC_INTERFACE
class Token(BaseModel):
    access_token: str
    token_type: str

# --- Note ---

# PUBLIC_INTERFACE
class NoteCreate(BaseModel):
    title: str = Field(..., description="Note title")
    content: Optional[str] = Field(default="", description="Initial note content (rich text supported)")
    youtube_url: Optional[str] = Field(default=None, description="YouTube URL to associate with this note")
    is_public: Optional[bool] = Field(default=False, description="Whether this note is public (shareable)")

# PUBLIC_INTERFACE
class NoteEdit(BaseModel):
    title: Optional[str]
    content: Optional[str]
    is_public: Optional[bool]

# PUBLIC_INTERFACE
class NoteOut(BaseModel):
    id: int
    title: str
    content: Optional[str]
    youtube_url: Optional[str]
    timestamps: Optional[str]
    is_public: bool
    created_at: str
    updated_at: str
    owner_id: int
    class Config:
        orm_mode = True

# --- Export format ---

# PUBLIC_INTERFACE
class NoteExportFormat(str):
    pdf = "pdf"
    txt = "txt"

# --- Share mode ---

# PUBLIC_INTERFACE
class NoteShareMode(BaseModel):
    mode: Literal["public", "private"] = Field(..., description="Sharing mode for note")
