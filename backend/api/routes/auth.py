"""Auth & User API routes — 用户注册/登录与信息管理.

Registered at /api/v1/auth and /api/v1/users
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

router = APIRouter()

# ── In-memory user store (MVP) — replace with DB in production ─────────────
_users_db: dict[str, dict] = {}
_sessions: dict[str, str] = {}  # token -> user_id


# ── Request models ─────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str


class LoginRequest(BaseModel):
    email: str
    password: str


class UserProfileResponse(BaseModel):
    user_id: str
    email: str
    name: str
    avatar: str | None = None
    role: str = "user"
    experience_years: int = 0
    education_level: str = ""
    skills: list[str] = Field(default_factory=list)
    career_goals: list[str] = Field(default_factory=list)
    preferred_locations: list[str] = Field(default_factory=list)
    preferred_industries: list[str] = Field(default_factory=list)
    salary_expectation: tuple[int, int] | None = None
    privacy_level: str = "basic"


class UpdateProfileRequest(BaseModel):
    name: str | None = None
    experience_years: int | None = None
    education_level: str | None = None
    skills: list[str] | None = None
    career_goals: list[str] | None = None
    preferred_locations: list[str] | None = None
    preferred_industries: list[str] | None = None
    privacy_level: str | None = None


# ── Helpers ────────────────────────────────────────────────────────────────

def _hash_password(pw: str) -> str:
    """MVP password hashing — replace with bcrypt in production."""
    import hashlib
    return hashlib.sha256(pw.encode()).hexdigest()


def _generate_token(user_id: str) -> str:
    import secrets
    token = secrets.token_urlsafe(32)
    _sessions[token] = user_id
    return token


def _get_current_user(token: str | None = None) -> dict | None:
    if not token:
        return None
    user_id = _sessions.get(token)
    if not user_id:
        return None
    return _users_db.get(user_id)


# ── Auth routes ────────────────────────────────────────────────────────────

@router.post("/register", response_model=dict, tags=["Auth"])
async def register(body: RegisterRequest):
    if body.email in {u["email"] for u in _users_db.values()}:
        raise HTTPException(status_code=400, detail="Email already registered")

    import uuid
    user_id = f"usr-{uuid.uuid4().hex[:8]}"
    user = {
        "user_id": user_id,
        "email": body.email,
        "password_hash": _hash_password(body.password),
        "name": body.name,
        "role": "user",
        "experience_years": 0,
        "education_level": "",
        "skills": [],
        "career_goals": [],
        "preferred_locations": [],
        "preferred_industries": [],
        "salary_expectation": None,
        "privacy_level": "basic",
    }
    _users_db[user_id] = user
    token = _generate_token(user_id)
    return {"token": token, "user": {k: v for k, v in user.items() if k != "password_hash"}}


@router.post("/login", response_model=dict, tags=["Auth"])
async def login(body: LoginRequest):
    user = next(
        (u for u in _users_db.values() if u["email"] == body.email),
        None,
    )
    if not user or user["password_hash"] != _hash_password(body.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = _generate_token(user["user_id"])
    return {"token": token, "user": {k: v for k, v in user.items() if k != "password_hash"}}


# ── User routes ────────────────────────────────────────────────────────────

@router.get("/me", response_model=UserProfileResponse, tags=["User"])
async def get_me(token: str | None = None):
    user = _get_current_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {k: v for k, v in user.items() if k != "password_hash"}


@router.patch("/me", response_model=UserProfileResponse, tags=["User"])
async def update_me(body: UpdateProfileRequest, token: str | None = None):
    user = _get_current_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    updates = body.model_dump(exclude_unset=True)
    for k, v in updates.items():
        user[k] = v
    return {k: v for k, v in user.items() if k != "password_hash"}


@router.get("/me/history", response_model=dict, tags=["User"])
async def get_history(token: str | None = None, page: int = 1, limit: int = 20):
    user = _get_current_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # MVP: return mock history
    mock_items = [
        {
            "id": f"hist-{i}",
            "type": "analysis" if i % 3 == 0 else "simulation" if i % 3 == 1 else "chat",
            "title": f"操作记录 #{i + 1}",
            "description": "这是一条示例操作记录",
            "created_at": "2025-05-10T12:00:00Z",
        }
        for i in range(5)
    ]
    return {"items": mock_items, "total": len(mock_items)}
