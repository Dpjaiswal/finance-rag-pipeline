from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.auth import LoginRequest, TokenResponse, UserCreate, UserRead
from app.services.auth import AuthService
from app.utils.responses import user_to_read

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=201)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> UserRead:
    user = AuthService(db).register(payload)
    return user_to_read(user)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    token, user = AuthService(db).authenticate(payload.email, payload.password)
    return TokenResponse(access_token=token, user=user_to_read(user))
