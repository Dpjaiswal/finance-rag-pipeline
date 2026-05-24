from app.models.user import User
from app.schemas.auth import UserRead


def user_to_read(user: User) -> UserRead:
    return UserRead(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
        is_active=user.is_active,
        company_id=user.company_id,
        company_name=user.company.name if user.company else None,
        roles=[role.name for role in user.roles],
        created_at=user.created_at,
    )
