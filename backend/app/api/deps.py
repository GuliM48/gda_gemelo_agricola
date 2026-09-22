from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models import User


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    db: Session = Depends(get_db),
) -> User:
    try:
        user = db.query(User).first()
    except Exception as exc:
        # Captura errores de conexión / decodificación (ej. mensaje de postgres en latin1)
        raise HTTPException(status_code=503, detail=f"Error de base de datos: {exc}") from exc
    if not user:
        # Auto-crear usuario de desarrollo si no existe ninguno (evita 401 en dev sin seed)
        try:
            user = User(
                username="dev_user",
                email="dev@gda.local",
                hashed_password="dev",
                role="Agrónomo",
                activo=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        except Exception:
            db.rollback()
            raise HTTPException(status_code=401, detail="Usuario no autenticado")
    return user


def get_current_active_user(
    db: Session = Depends(get_db),
) -> User:
    user = get_current_user(db)
    if not user.activo:
        raise HTTPException(status_code=403, detail="Usuario inactivo")
    return user
