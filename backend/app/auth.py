import hashlib
import secrets
import smtplib
import ssl
import time
from email.message import EmailMessage
from typing import Annotated

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session as DBSession

from .config import settings
from .db import get_db
from .models import AuthToken, RateBucket, Session, User, UserProfile

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
Db = Annotated[DBSession, Depends(get_db)]
hasher = PasswordHasher()
dummy_hash = hasher.hash(secrets.token_hex(24))


def digest(token):
    return hashlib.sha256(token.encode()).hexdigest()


def limit(db, key, maximum=15, window=300):
    key = digest(key + ":" + str(int(time.time() // window)))
    row = db.get(RateBucket, key)
    if row is None:
        row = RateBucket(key=key, count=0, expires_at=time.time() + window)
        db.add(row)
        db.flush()
    count = db.execute(
        update(RateBucket).where(RateBucket.key == key).values(count=RateBucket.count + 1).returning(RateBucket.count)
    ).scalar_one()
    db.commit()
    if count > maximum:
        raise HTTPException(429, "Too many requests. Please try again later.", headers={"Retry-After": str(window)})


def current_user(request: Request, db: Db):
    token = request.cookies.get("prepforge_session", "")
    session = db.scalar(select(Session).where(Session.token_hash == digest(token), Session.expires_at > time.time()))
    if not session:
        raise HTTPException(401, "Please sign in to continue.")
    user = db.get(User, session.user_id)
    if not user or not user.active:
        raise HTTPException(401, "This account is unavailable.")
    if request.method not in ("GET", "HEAD", "OPTIONS"):
        if not secrets.compare_digest(request.headers.get("x-csrf-token", ""), session.csrf):
            raise HTTPException(403, "Security token expired. Refresh and try again.")
    request.state.session = session
    return user


CurrentUser = Annotated[User, Depends(current_user)]


def admin_user(user: CurrentUser):
    if user.role != "admin":
        raise HTTPException(403, "Administrator access required.")
    return user


Admin = Annotated[User, Depends(admin_user)]


def public_user(user, db):
    profile = db.scalar(select(UserProfile).where(UserProfile.user_id == user.id))
    return {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "email_verified": user.email_verified,
        "role": user.role,
        "profile": profile.details if profile else {},
    }


def sign_in(user, response, db, remember=True):
    token, csrf = secrets.token_urlsafe(40), secrets.token_urlsafe(32)
    lifetime = 30 * 86400 if remember else 86400
    db.add(Session(user_id=user.id, token_hash=digest(token), csrf=csrf, expires_at=time.time() + lifetime))
    user.last_login = time.time()
    db.commit()
    response.set_cookie(
        "prepforge_session",
        token,
        httponly=True,
        secure=settings().app_env == "production",
        samesite="lax",
        max_age=lifetime if remember else None,
        path="/",
    )
    return {"user": public_user(user, db), "csrf": csrf}


class Credentials(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    remember: bool = True


class Signup(Credentials):
    full_name: str = Field(min_length=2, max_length=120)


class EmailRequest(BaseModel):
    email: EmailStr


class TokenRequest(BaseModel):
    token: str = Field(min_length=20, max_length=200)
    password: str = Field(default="", max_length=128)


class PasswordChange(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=10, max_length=128)


def issue_email(user, purpose, db):
    token = secrets.token_urlsafe(40)
    db.add(AuthToken(user_id=user.id, token_hash=digest(token), purpose=purpose, expires_at=time.time() + 3600))
    db.commit()
    path = "reset-password" if purpose == "reset" else "verify-email"
    url = f"{settings().frontend_origin}/{path}?token={token}"
    if settings().email_host:
        message = EmailMessage()
        message["From"], message["To"] = settings().email_from, user.email
        message["Subject"] = "PrepFaang: reset password" if purpose == "reset" else "Verify your PrepFaang email"
        message.set_content(f"Open this link within one hour: {url}")
        try:
            with smtplib.SMTP(settings().email_host, settings().email_port, timeout=10) as smtp:
                smtp.starttls(context=ssl.create_default_context())
                if settings().email_user:
                    smtp.login(settings().email_user, settings().email_password)
                smtp.send_message(message)
        except (OSError, smtplib.SMTPException):
            raise HTTPException(503, "Email delivery is unavailable. Please try again later.")
    elif settings().app_env != "production":
        # Local development only; never returned by a production API.
        return url
    return None


@router.post("/signup", status_code=201)
def signup(data: Signup, request: Request, response: Response, db: Db):
    limit(db, "signup:" + request.client.host)
    email = str(data.email).lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(409, "An account with this email already exists.")
    user = User(email=email, full_name=data.full_name.strip(), password_hash=hasher.hash(data.password))
    db.add(user)
    db.flush()
    db.add(UserProfile(user_id=user.id, details={}))
    db.commit()
    return sign_in(user, response, db, data.remember)


@router.post("/login")
def login(data: Credentials, request: Request, response: Response, db: Db):
    limit(db, "login-ip:" + request.client.host, 30)
    limit(db, "login-account:" + str(data.email).lower(), 10)
    # Keep password verification/session creation ordered with password changes.
    user = db.scalar(select(User).where(User.email == str(data.email).lower()).with_for_update())
    try:
        valid = hasher.verify(user.password_hash if user else dummy_hash, data.password)
    except VerificationError:
        valid = False
    if not user or not valid or not user.active:
        raise HTTPException(401, "Email or password is incorrect.")
    return sign_in(user, response, db, data.remember)


@router.get("/me")
def me(user: CurrentUser, request: Request, db: Db):
    return {"user": public_user(user, db), "csrf": request.state.session.csrf}


@router.post("/logout")
def logout(user: CurrentUser, request: Request, response: Response, db: Db):
    db.delete(request.state.session)
    db.commit()
    response.delete_cookie("prepforge_session", path="/")
    return {"message": "Signed out."}


@router.post("/logout-all")
def logout_all(user: CurrentUser, response: Response, db: Db):
    db.scalar(select(User).where(User.id == user.id).with_for_update())
    db.execute(delete(Session).where(Session.user_id == user.id))
    db.commit()
    response.delete_cookie("prepforge_session", path="/")
    return {"message": "Signed out on all devices. Please sign in again."}


@router.post("/change-password")
def change_password(data: PasswordChange, user: CurrentUser, response: Response, db: Db):
    limit(db, "change-password:" + user.id, 5)
    # Serialize password changes; re-read after locking so concurrent changes cannot
    # authenticate with a stale password loaded earlier by current_user.
    db.scalar(select(User).where(User.id == user.id).with_for_update())
    db.refresh(user)
    try:
        valid = hasher.verify(user.password_hash, data.current_password)
    except VerificationError:
        valid = False
    if not valid or not user.active:
        raise HTTPException(400, "Current password is incorrect or account is unavailable.")
    if data.current_password == data.new_password:
        raise HTTPException(422, "Choose a new password different from your current password.")
    user.password_hash = hasher.hash(data.new_password)
    db.execute(delete(Session).where(Session.user_id == user.id))
    db.execute(delete(AuthToken).where(AuthToken.user_id == user.id))
    db.commit()
    response.delete_cookie("prepforge_session", path="/")
    return {"message": "Password changed. Sign in again on each device."}


@router.post("/forgot-password")
def forgot(data: EmailRequest, request: Request, db: Db):
    limit(db, "reset:" + request.client.host, 5)
    user = db.scalar(select(User).where(User.email == str(data.email).lower()))
    link = issue_email(user, "reset", db) if user else None
    result = {"message": "If an account exists, a reset link has been sent."}
    if link:
        result["development_link"] = link
    return result


@router.post("/send-verification")
def send_verification(user: CurrentUser, db: Db):
    limit(db, "verify:" + user.id, 5)
    link = issue_email(user, "verify", db)
    return {"message": "Verification email sent.", **({"development_link": link} if link else {})}


def consume(token, purpose, db):
    record = db.scalar(
        select(AuthToken).where(AuthToken.token_hash == digest(token), AuthToken.purpose == purpose).with_for_update()
    )
    if not record or record.used or record.expires_at <= time.time():
        raise HTTPException(400, "This link has expired or has already been used.")
    record.used = True
    return db.get(User, record.user_id)


@router.post("/reset-password")
def reset(data: TokenRequest, db: Db):
    if len(data.password) < 10:
        raise HTTPException(422, "Use at least 10 characters.")
    user = consume(data.token, "reset", db)
    user.password_hash = hasher.hash(data.password)
    db.execute(delete(Session).where(Session.user_id == user.id))
    db.execute(delete(AuthToken).where(AuthToken.user_id == user.id))
    db.commit()
    return {"message": "Password updated. Please sign in."}


@router.post("/verify-email")
def verify(data: TokenRequest, db: Db):
    user = consume(data.token, "verify", db)
    user.email_verified = True
    db.commit()
    return {"message": "Your email is verified."}
