from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlmodel import Session, select

from app.api import deps
from app.core.config import settings
from app.core.db import get_db
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User

router = APIRouter()


class Token(BaseModel):
    access_token: str
    token_type: str


class UserCreate(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: str
    username: str
    is_active: bool


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], session: Session = Depends(get_db)
) -> Token:
    statement = select(User).where(User.username == form_data.username)
    user = session.exec(statement).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    return Token(access_token=access_token, token_type="bearer")


@router.post("/register", response_model=UserResponse)
async def register(user_in: UserCreate, session: Session = Depends(get_db)):
    if len(user_in.password) < 8:
        raise HTTPException(status_code=400, detail="密码长度至少需要 8 个字符")

    if len(user_in.username) < 3:
        raise HTTPException(status_code=400, detail="用户名长度至少需要 3 个字符")

    statement = select(User).where(User.username == user_in.username)
    existing_user = session.exec(statement).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="该用户名已被注册")

    user = User(username=user_in.username, hashed_password=get_password_hash(user_in.password), is_active=True)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@router.get("/users/me", response_model=UserResponse)
async def read_users_me(current_user: Annotated[User, Depends(deps.get_current_active_user)]):
    return current_user


@router.delete("/users/me", status_code=204)
async def delete_user(
    current_user: Annotated[User, Depends(deps.get_current_active_user)], session: Session = Depends(get_db)
):
    """Delete the current user account."""
    session.delete(current_user)
    session.commit()
    return None
