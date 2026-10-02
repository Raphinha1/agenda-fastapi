from pydantic import EmailStr, field_validator
from sqlmodel import Field, SQLModel


class ContactoBase(SQLModel):
    nombre: str = Field(min_length=2, max_length=50)
    telefono: str
    mail: EmailStr

    @field_validator("telefono")
    @classmethod
    def telefono_valido(cls, value: str) -> str:
        if not (7 <= len(value) <= 15 and value.isascii() and value.isdecimal()):
            raise ValueError("El teléfono debe contener entre 7 y 15 dígitos")
        return value


class Contacto(ContactoBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="usuario.id", index=True)


class ContactoCreate(ContactoBase):
    pass


class ContactoUpdate(SQLModel):
    nombre: str | None = Field(default=None, min_length=2, max_length=50)
    telefono: str | None = None
    mail: EmailStr | None = None

    @field_validator("telefono")
    @classmethod
    def telefono_valido(cls, value: str | None) -> str | None:
        return ContactoBase.telefono_valido(value) if value is not None else None


class ContactoPublic(ContactoBase):
    id: int
