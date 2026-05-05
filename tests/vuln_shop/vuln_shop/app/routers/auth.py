from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel
from ..database import get_db, User
from ..auth import hash_password, verify_password, create_access_token
import secrets

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    referral_code: str = ""


@router.post("/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(400, "Username already taken")

    user = User(
        username=req.username,
        email=req.email,
        hashed_pw=hash_password(req.password),
        balance=100.0,  # 가입 보너스
        referral_code=secrets.token_hex(4).upper(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    if req.referral_code:
        # BUG-4: 자기 추천 체크 없음 — auth 레이어에도 동일하게 존재
        referrer = db.query(User).filter(
            User.referral_code == req.referral_code
        ).first()
        if referrer:
            referrer.balance += 10.0
            user.balance     += 5.0
            referrer.referral_count += 1
            db.commit()

    return {"id": user.id, "referral_code": user.referral_code}


@router.post("/login")
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.username == form.username).first()
    if not user or not verify_password(form.password, user.hashed_pw):
        raise HTTPException(401, "Invalid credentials")

    token = create_access_token(user.id, user.role)
    return {"access_token": token, "token_type": "bearer"}
