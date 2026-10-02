import secrets
from pathlib import Path

import jwt
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlmodel import Session, select

from src.auth.dependencies import user_from_token
from src.auth.security import create_access_token, decode_access_token
from src.config import ACCESS_TOKEN_EXPIRE_MINUTES
from src.database import get_session
from src.models.agenda import Contacto, ContactoCreate
from src.routers.auth import authenticate_user


router = APIRouter(prefix="/views", tags=["Vistas Web (Jinja2)"])
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parents[1] / "templates"))
COOKIE_NAME = "agenda_session"


def web_identity(request: Request, session: Session):
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    try:
        user = user_from_token(token, session)
        csrf = decode_access_token(token).get("csrf")
        if not isinstance(csrf, str):
            return None
        return user, csrf
    except (HTTPException, jwt.PyJWTError):
        return None


def agenda_page(request: Request, session: Session, user, csrf: str, error: str | None = None):
    contacts = session.exec(select(Contacto).where(Contacto.user_id == user.id)).all()
    return templates.TemplateResponse(
        request,
        "agenda.html",
        {"contactos": contacts, "user": user, "csrf": csrf, "error": error},
    )


@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {"error": None})


@router.post("/login")
def web_login(
    request: Request,
    username: str = Form(),
    password: str = Form(),
    session: Session = Depends(get_session),
):
    user = authenticate_user(session, username, password)
    if user is None:
        return templates.TemplateResponse(
            request,
            "login.html",
            {"error": "Usuario o contraseña incorrectos"},
            status_code=401,
        )
    token = create_access_token({"sub": user.username, "csrf": secrets.token_urlsafe(32)})
    response = RedirectResponse("/views/agenda", status_code=303)
    response.set_cookie(
        COOKIE_NAME,
        token,
        httponly=True,
        secure=request.url.scheme == "https",
        samesite="strict",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    return response


@router.get("/agenda")
def render_agenda_view(request: Request, session: Session = Depends(get_session)):
    identity = web_identity(request, session)
    if identity is None:
        return RedirectResponse("/views/login", status_code=303)
    user, csrf = identity
    return agenda_page(request, session, user, csrf)


@router.post("/agenda")
def agregar_contacto_web(
    request: Request,
    nombre: str = Form(),
    telefono: str = Form(),
    mail: str = Form(),
    csrf: str = Form(),
    session: Session = Depends(get_session),
):
    identity = web_identity(request, session)
    if identity is None:
        return RedirectResponse("/views/login", status_code=303)
    user, expected_csrf = identity
    if not secrets.compare_digest(csrf, expected_csrf):
        raise HTTPException(status_code=403, detail="Formulario no válido")
    try:
        contact_in = ContactoCreate(nombre=nombre, telefono=telefono, mail=mail)
    except ValidationError:
        return agenda_page(request, session, user, expected_csrf, "Revisa los datos del contacto")
    contact = Contacto.model_validate(contact_in, update={"user_id": user.id})
    session.add(contact)
    session.commit()
    return RedirectResponse("/views/agenda", status_code=303)


@router.post("/logout")
def web_logout(request: Request, csrf: str = Form(), session: Session = Depends(get_session)):
    identity = web_identity(request, session)
    if identity is None:
        return RedirectResponse("/views/login", status_code=303)
    _, expected_csrf = identity
    if not secrets.compare_digest(csrf, expected_csrf):
        raise HTTPException(status_code=403, detail="Formulario no válido")
    response = RedirectResponse("/views/login", status_code=303)
    response.delete_cookie(COOKIE_NAME)
    return response
