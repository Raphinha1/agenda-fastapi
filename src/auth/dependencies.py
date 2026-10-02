import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select

from src.auth.security import decode_access_token
from src.database import get_session
from src.models.user import Usuario


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def user_from_token(token: str, session: Session) -> Usuario:
    error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        username = payload.get("sub")
        if not isinstance(username, str) or not username:
            raise error
    except jwt.PyJWTError as exc:
        raise error from exc
    user = session.exec(select(Usuario).where(Usuario.username == username)).first()
    if user is None:
        raise error
    return user


def get_current_user(
    token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)
) -> Usuario:
    return user_from_token(token, session)
