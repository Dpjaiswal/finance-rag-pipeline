from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.company import Company
from app.models.user import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_email(self, email: str) -> User | None:
        return self.db.scalar(
            select(User).where(User.email == email).options(selectinload(User.roles), selectinload(User.company))
        )

    def get(self, user_id: int) -> User | None:
        return self.db.scalar(
            select(User).where(User.id == user_id).options(selectinload(User.roles), selectinload(User.company))
        )

    def get_or_create_company(self, name: str) -> Company:
        company = self.db.scalar(select(Company).where(Company.name == name))
        if company:
            return company
        company = Company(name=name)
        self.db.add(company)
        self.db.flush()
        return company

    def create(self, user: User) -> User:
        self.db.add(user)
        self.db.flush()
        self.db.refresh(user)
        return user
