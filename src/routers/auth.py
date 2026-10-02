from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from src.auth.security import create_access_token, get_password_hash, verify_password
from src.database import get_session
from src.models.user import Token, Usuario, UsuarioCreate, UsuarioPublic


router = APIRouter(prefix="/auth", tags=["Autenticación"])


def authenticate_user(session: Session, username: str, password: str) -> Usuario | None:
    user = session.exec(select(Usuario).where(Usuario.username == username)).first()
    if user is None or not verify_password(password, user.hashed_password):
        return None
    return user


@router.post("/register", response_model=UsuarioPublic, status_code=201)
def register(user_data: UsuarioCreate, session: Session = Depends(get_session)):
    if len(user_data.password.encode("utf-8")) > 72:
        raise HTTPException(status_code=422, detail="La contraseña excede 72 bytes")
    user = Usuario(
        username=user_data.username,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
    )
    session.add(user)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(status_code=409, detail="Usuario o correo ya registrado") from exc
    session.refresh(user)
    return user


@router.post("/token", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
):
    user = authenticate_user(session, form_data.username, form_data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"access_token": create_access_token({"sub": user.username}), "token_type": "bearer"}
