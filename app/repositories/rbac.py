from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.rbac import Permission, Role


class RbacRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_role_by_name(self, name: str) -> Role | None:
        return self.db.scalar(select(Role).where(Role.name == name).options(selectinload(Role.permissions)))

    def get_role(self, role_id: int) -> Role | None:
        return self.db.scalar(select(Role).where(Role.id == role_id).options(selectinload(Role.permissions)))

    def get_permission_by_code(self, code: str) -> Permission | None:
        return self.db.scalar(select(Permission).where(Permission.code == code))

    def list_permissions_by_codes(self, codes: list[str]) -> list[Permission]:
        if not codes:
            return []
        return list(self.db.scalars(select(Permission).where(Permission.code.in_(codes))))

    def create_role(self, role: Role) -> Role:
        self.db.add(role)
        self.db.flush()
        self.db.refresh(role)
        return role
