from pydantic import EmailStr
from sqlmodel import Field, SQLModel


class Usuario(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True, min_length=3, max_length=50)
    email: EmailStr = Field(index=True, unique=True)
    hashed_password: str


class UsuarioCreate(SQLModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8)


class UsuarioPublic(SQLModel):
    id: int
    username: str
    email: EmailStr


class Token(SQLModel):
    access_token: str
    token_type: str
