from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories.users import UserRepository
from app.schemas.auth import UserCreate
from app.services.audit import AuditService


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)
        self.audit = AuditService(db)

    def register(self, payload: UserCreate) -> User:
        if self.users.get_by_email(payload.email):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already registered")
        company = self.users.get_or_create_company(payload.company_name)
        user = User(
            full_name=payload.full_name,
            email=payload.email.lower(),
            password_hash=hash_password(payload.password),
            company_id=company.id,
        )
        self.users.create(user)
        self.audit.log(user_id=user.id, action="auth.register", target_type="user", target_id=user.id)
        self.db.commit()
        return self.users.get(user.id) or user

    def authenticate(self, email: str, password: str) -> tuple[str, User]:
        user = self.users.get_by_email(email.lower())
        if not user or not verify_password(password, user.password_hash) or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        token = create_access_token(str(user.id), {"email": user.email})
        self.audit.log(user_id=user.id, action="auth.login", target_type="user", target_id=user.id)
        self.db.commit()
        return token, user
