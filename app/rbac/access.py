from app.models.user import User


ADMIN_ROLE = "Admin"


def is_admin(user: User) -> bool:
    return any(role.name == ADMIN_ROLE for role in user.roles)


def user_company_name(user: User) -> str | None:
    return user.company.name if user.company else None
