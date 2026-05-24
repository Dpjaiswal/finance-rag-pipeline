from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.db.session import get_db
from app.models.user import User
from app.rbac.permissions import PermissionCode
from app.repositories.users import UserRepository
from app.schemas.rbac import AssignRoleRequest, PermissionRead, RoleCreate, RoleRead
from app.services.rbac import RbacService

router = APIRouter(tags=["rbac"])


def role_to_read(role) -> RoleRead:
    return RoleRead(
        id=role.id,
        name=role.name,
        description=role.description,
        permissions=[permission.code for permission in role.permissions],
    )


@router.post("/roles/create", response_model=RoleRead, status_code=201)
def create_role(
    payload: RoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionCode.roles_create)),
) -> RoleRead:
    return role_to_read(RbacService(db).create_role(payload, current_user))


@router.post("/users/assign-role", response_model=dict)
def assign_role(
    payload: AssignRoleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionCode.users_assign_role)),
) -> dict:
    user = RbacService(db).assign_role(
        user_id=payload.user_id, role_id=payload.role_id, role_name=payload.role_name, actor=current_user
    )
    return {"user_id": user.id, "roles": [role.name for role in user.roles]}


@router.get("/users/{user_id}/roles", response_model=list[RoleRead])
def get_user_roles(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PermissionCode.users_read)),
) -> list[RoleRead]:
    user = UserRepository(db).get(user_id)
    return [role_to_read(role) for role in user.roles] if user else []


@router.get("/users/{user_id}/permissions", response_model=list[PermissionRead])
def get_user_permissions(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(PermissionCode.users_read)),
) -> list[PermissionRead]:
    user = UserRepository(db).get(user_id)
    if not user:
        return []
    return [
        PermissionRead(code=permission.code, description=permission.description)
        for role in user.roles
        for permission in role.permissions
    ]
