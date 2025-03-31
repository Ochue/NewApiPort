from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from models import User
from database import SessionLocal
from jose import JWTError, jwt

# Dependencia para obtener la base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Dependencia para obtener el usuario actual
def get_current_user(db: Session = Depends(get_db)):
    user = db.query(User).first()  # Obtén al primer usuario, ajusta según lo que necesites
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
