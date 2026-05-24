from datetime import datetime

from pydantic import AliasChoices, BaseModel, Field, field_validator

DEFAULT_COMPANY_NAME = "Default Company"


class UserCreate(BaseModel):
    full_name: str = Field(
        min_length=1,
        max_length=255,
        validation_alias=AliasChoices("full_name", "name"),
        description="User display name. Accepts either full_name or name.",
    )
    email: str = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    company_name: str = Field(
        default=DEFAULT_COMPANY_NAME,
        min_length=1,
        max_length=255,
        description="Tenant/company name. Optional for simple registration flows.",
    )

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        if "@" not in value or "." not in value.rsplit("@", 1)[-1]:
            raise ValueError("Invalid email address")
        return value.lower()


class UserRead(BaseModel):
    id: int
    full_name: str
    email: str
    is_active: bool
    company_id: int | None
    company_name: str | None = None
    roles: list[str] = []
    created_at: datetime

    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        if "@" not in value or "." not in value.rsplit("@", 1)[-1]:
            raise ValueError("Invalid email address")
        return value.lower()


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead
