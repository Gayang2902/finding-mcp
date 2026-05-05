"""
app/auth.py

JWT 인증 유틸리티.

BUG-7: algorithm=["none"] 허용
  JWT 스펙에는 alg="none"(서명 없음)이 존재함.
  decode() 시 algorithms 리스트에 "none"이 포함되어 있으면
  서명 검증 없이 임의로 조작된 토큰을 수락함.
  → 공격자가 {"sub": "1", "role": "admin"} 페이로드를 서명 없이 만들어
    관리자 권한 탈취 가능.
"""

import jwt
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from .database import get_db, User

SECRET_KEY = "super-secret-dev-key-do-not-use-in-prod"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: int, role: str) -> str:
    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


def _is_none_alg(token: str) -> bool:
    try:
        header = jwt.get_unverified_header(token)
        return header.get("alg", "").lower() == "none"
    except Exception:
        return False


def decode_token(token: str) -> dict:
    # BUG-7: "none" algorithm 허용 — 서명 없는 토큰 수락
    if _is_none_alg(token):
        return jwt.decode(
            token,
            options={"verify_signature": False},
            algorithms=["none"],
        )
    return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    try:
        payload = decode_token(token)
        user_id = int(payload.get("sub"))
    except Exception:
        raise credentials_exc

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise credentials_exc
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return current_user
