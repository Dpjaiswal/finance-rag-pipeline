from sqlalchemy import select

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.company import Company
from app.models.rbac import Permission, Role
from app.models.user import User
from app.rbac.permissions import PermissionCode


ROLE_PERMISSIONS = {
    "Admin": [code.value for code in PermissionCode],
    "Financial Analyst": [
        "documents:upload",
        "documents:edit",
        "documents:view",
        "documents:search",
        "rag:index",
        "rag:remove",
        "rag:search",
        "rag:context",
    ],
    "Auditor": ["documents:view", "documents:search", "rag:search", "rag:context"],
    "Client": ["documents:view", "rag:context"],
}


def add_seed_user(
    users: list[tuple[str, str, str, str, str]],
    *,
    email: str | None,
    password: str | None,
    full_name: str,
    company_name: str,
    role_name: str,
) -> None:
    if email and password:
        users.append((email, full_name, password, company_name, role_name))


def seed() -> None:
    settings = get_settings()
    with SessionLocal() as db:
        permissions: dict[str, Permission] = {}
        for code in PermissionCode:
            permission = db.scalar(select(Permission).where(Permission.code == code.value))
            if not permission:
                permission = Permission(code=code.value, description=code.value.replace(":", " "))
                db.add(permission)
            permissions[code.value] = permission
        db.flush()

        roles: dict[str, Role] = {}
        for name, codes in ROLE_PERMISSIONS.items():
            role = db.scalar(select(Role).where(Role.name == name))
            if not role:
                role = Role(name=name, description=f"Default {name} role")
                db.add(role)
            role.permissions = [permissions[code] for code in codes]
            roles[name] = role
        db.flush()

        company_names = ["Acme Finance", "Globex Capital"]
        companies = {}
        for name in company_names:
            company = db.scalar(select(Company).where(Company.name == name))
            if not company:
                company = Company(name=name)
                db.add(company)
            companies[name] = company
        db.flush()

        samples: list[tuple[str, str, str, str, str]] = []
        add_seed_user(
            samples,
            email=settings.default_admin_email,
            password=settings.default_admin_password,
            full_name="System Admin",
            company_name="Acme Finance",
            role_name="Admin",
        )
        add_seed_user(
            samples,
            email=settings.seed_analyst_email,
            password=settings.seed_analyst_password,
            full_name="Finance Analyst",
            company_name="Acme Finance",
            role_name="Financial Analyst",
        )
        add_seed_user(
            samples,
            email=settings.seed_auditor_email,
            password=settings.seed_auditor_password,
            full_name="Audit User",
            company_name="Acme Finance",
            role_name="Auditor",
        )
        add_seed_user(
            samples,
            email=settings.seed_client_email,
            password=settings.seed_client_password,
            full_name="Client User",
            company_name="Globex Capital",
            role_name="Client",
        )
        for email, full_name, password, company_name, role_name in samples:
            user = db.scalar(select(User).where(User.email == email))
            if not user:
                user = User(
                    email=email,
                    full_name=full_name,
                    password_hash=hash_password(password),
                    company_id=companies[company_name].id,
                )
                db.add(user)
            user.roles = [roles[role_name]]
        db.commit()


if __name__ == "__main__":
    seed()
