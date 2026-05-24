from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.rbac import Role
from app.models.user import User
from app.repositories.rbac import RbacRepository
from app.repositories.users import UserRepository
from app.schemas.rbac import RoleCreate
from app.services.audit import AuditService


class RbacService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = RbacRepository(db)
        self.users = UserRepository(db)
        self.audit = AuditService(db)

    def create_role(self, payload: RoleCreate, actor: User) -> Role:
        if self.repo.get_role_by_name(payload.name):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Role already exists")
        permissions = self.repo.list_permissions_by_codes(payload.permission_codes)
        missing = set(payload.permission_codes) - {p.code for p in permissions}
        if missing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown permissions: {sorted(missing)}")
        role = Role(name=payload.name, description=payload.description, permissions=permissions)
        self.repo.create_role(role)
        self.audit.log(user_id=actor.id, action="rbac.create_role", target_type="role", target_id=role.id)
        self.db.commit()
        return role

    def assign_role(self, *, user_id: int, role_id: int | None, role_name: str | None, actor: User) -> User:
        user = self.users.get(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        role = self.repo.get_role(role_id) if role_id else self.repo.get_role_by_name(role_name or "")
        if not role:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
        if role not in user.roles:
            user.roles.append(role)
        self.audit.log(
            user_id=actor.id,
            action="rbac.assign_role",
            target_type="user",
            target_id=user.id,
            metadata={"role": role.name},
        )
        self.db.commit()
        return self.users.get(user.id) or user

    @staticmethod
    def permission_codes(user: User) -> list[str]:
        return sorted({permission.code for role in user.roles for permission in role.permissions})
