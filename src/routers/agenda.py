from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from src.auth.dependencies import get_current_user
from src.database import get_session
from src.models.agenda import Contacto, ContactoCreate, ContactoPublic, ContactoUpdate
from src.models.user import Usuario


router = APIRouter(prefix="/agenda", tags=["Agenda CRUD"])


def own_contact(session: Session, contact_id: int, user_id: int) -> Contacto:
    contact = session.exec(
        select(Contacto).where(Contacto.id == contact_id, Contacto.user_id == user_id)
    ).first()
    if contact is None:
        raise HTTPException(status_code=404, detail="Contacto no encontrado")
    return contact


@router.get("", response_model=list[ContactoPublic])
def get_contactos(
    session: Session = Depends(get_session), user: Usuario = Depends(get_current_user)
):
    return session.exec(select(Contacto).where(Contacto.user_id == user.id)).all()


@router.get("/{contact_id}", response_model=ContactoPublic)
def get_contacto(
    contact_id: int,
    session: Session = Depends(get_session),
    user: Usuario = Depends(get_current_user),
):
    return own_contact(session, contact_id, user.id)


@router.post("", response_model=ContactoPublic, status_code=status.HTTP_201_CREATED)
def crear_contacto(
    contact_in: ContactoCreate,
    session: Session = Depends(get_session),
    user: Usuario = Depends(get_current_user),
):
    contact = Contacto.model_validate(contact_in, update={"user_id": user.id})
    session.add(contact)
    session.commit()
    session.refresh(contact)
    return contact


@router.put("/{contact_id}", response_model=ContactoPublic)
def actualizar_contacto(
    contact_id: int,
    contact_in: ContactoUpdate,
    session: Session = Depends(get_session),
    user: Usuario = Depends(get_current_user),
):
    contact = own_contact(session, contact_id, user.id)
    changes = contact_in.model_dump(exclude_unset=True)
    if any(value is None for value in changes.values()):
        raise HTTPException(status_code=422, detail="Los campos no pueden ser nulos")
    for key, value in changes.items():
        setattr(contact, key, value)
    session.add(contact)
    session.commit()
    session.refresh(contact)
    return contact


@router.delete("/{contact_id}")
def eliminar_contacto(
    contact_id: int,
    session: Session = Depends(get_session),
    user: Usuario = Depends(get_current_user),
):
    contact = own_contact(session, contact_id, user.id)
    session.delete(contact)
    session.commit()
    return {"mensaje": f"Contacto {contact_id} eliminado correctamente"}
