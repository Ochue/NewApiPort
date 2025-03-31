from fastapi import FastAPI, Depends, HTTPException, status, File, Form, UploadFile
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import User, Portfolio, Project
from passlib.context import CryptContext
from pydantic import BaseModel
import jwt
from datetime import datetime, timedelta
from typing import List
from io import BytesIO
import os

# Crear la base de datos
from database import Base
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Configuración de seguridad
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "mi_secreto"
ALGORITHM = "HS256"

# Dependencia para obtener la sesión de la base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Modelo Pydantic para login
class LoginRequest(BaseModel):
    email: str
    password: str

# Modelo Pydantic para token de respuesta
class TokenResponse(BaseModel):
    access_token: str
    token_type: str

# Modelo Pydantic para registro de usuario
class UserCreate(BaseModel):
    full_name: str
    email: str
    password: str

# Modelo Pydantic para respuesta de usuario
class UserResponse(BaseModel):
    id: int
    full_name: str
    email: str

# Función para generar un token JWT
def create_jwt_token(user_id: int):
    payload = {
        "sub": str(user_id),
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

# Función para verificar contraseña
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Función para obtener usuario autenticado
def get_current_user(token: str, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
        return user
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")

# Ruta para registrar un usuario
@app.post("/register", response_model=UserResponse)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="El usuario ya existe")

    hashed_password = pwd_context.hash(user_data.password)
    new_user = User(full_name=user_data.full_name, email=user_data.email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user

# Ruta para login y generación de token
@app.post("/login", response_model=TokenResponse)
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales incorrectas")

    token = create_jwt_token(user.id)
    return {"access_token": token, "token_type": "bearer"}

# Ruta para crear un portafolio (aceptando datos y archivos en multipart/form-data)
@app.post("/create_portfolio/")
async def create_portfolio(
    description: str = Form(...),
    languages: str = Form(...),
    cv: UploadFile = File(...),  # CV como archivo
    projects: List[UploadFile] = File(...),  # Proyectos como lista de imágenes
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Guardamos el CV en un directorio, y almacenamos la ruta
    cv_directory = "static/cvs"
    os.makedirs(cv_directory, exist_ok=True)
    cv_path = os.path.join(cv_directory, cv.filename)
    with open(cv_path, "wb") as f:
        f.write(await cv.read())

    # Crear el portafolio
    new_portfolio = Portfolio(
        user_id=current_user.id,
        description=description,
        languages=languages,
        cv=cv_path  # Guardamos la ruta del archivo
    )
    db.add(new_portfolio)
    db.commit()
    db.refresh(new_portfolio)

    # Guardar imágenes de los proyectos
    project_directory = "static/projects"
    os.makedirs(project_directory, exist_ok=True)

    for project_image in projects:
        project_image_path = os.path.join(project_directory, project_image.filename)
        with open(project_image_path, "wb") as f:
            f.write(await project_image.read())

        # Crear el proyecto asociado con la imagen
        new_project = Project(
            portfolio_id=new_portfolio.id,
            name=project_image.filename,  # Asignamos el nombre de la imagen como nombre del proyecto
            image=project_image_path  # Ruta de la imagen
        )
        db.add(new_project)
        db.commit()

    return {"message": "Portafolio creado exitosamente", "portfolio_id": new_portfolio.id}

