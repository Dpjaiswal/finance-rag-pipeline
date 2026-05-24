from pydantic import BaseModel, Field


class RoleCreate(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    description: str | None = None
    permission_codes: list[str] = []


class RoleRead(BaseModel):
    id: int
    name: str
    description: str | None = None
    permissions: list[str] = []


class AssignRoleRequest(BaseModel):
    user_id: int
    role_id: int | None = None
    role_name: str | None = None


class PermissionRead(BaseModel):
    code: str
    description: str | None = None
