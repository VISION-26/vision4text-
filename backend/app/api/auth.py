from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.models.user import User
from app.schemas.user import RefreshTokenRequest, TokenResponse, UserCreate, UserLogin, UserResponse, UserUpdate
from app.services.history_service import HistoryService
from app.services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    if not settings.ALLOW_PUBLIC_REGISTRATION:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Public registration is disabled. Ask an administrator to create the account.")
    user = await UserService.create_user(db, user_in)
    await HistoryService.log_action(db, user.id, "REGISTER", "User account created")
    return user


@router.post("/login", response_model=TokenResponse)
async def login(user_in: UserLogin, db: AsyncSession = Depends(get_db)):
    user = await UserService.authenticate(db, user_in.email, user_in.password)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password.")
    await HistoryService.log_action(db, user.id, "LOGIN", "User signed in")
    return TokenResponse(access_token=create_access_token(user.id, user.role), refresh_token=create_refresh_token(user.id), user=UserResponse.model_validate(user))


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(req: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    payload = decode_token(req.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token.")
    user = await UserService.get_by_id(db, int(payload["sub"]))
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User unavailable.")
    return TokenResponse(access_token=create_access_token(user.id, user.role), refresh_token=create_refresh_token(user.id), user=UserResponse.model_validate(user))


@router.get("/profile", response_model=UserResponse)
async def get_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/profile", response_model=UserResponse)
async def update_profile(user_in: UserUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    user_in.role = None
    user_in.is_active = None
    return await UserService.update_user(db, current_user.id, user_in)
