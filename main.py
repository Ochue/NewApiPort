from fastapi import FastAPI, Depends, HTTPException, status, File, Form, UploadFile
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import User, Portfolio, Project, SocialNetwork
from passlib.context import CryptContext
from pydantic import BaseModel
import jwt
from datetime import datetime, timedelta
import os
import logging

# Crear la base de datos
from database import Base
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Configuración de seguridad
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "mi_secreto"
ALGORITHM = "HS256"

# Configuración de logs
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# Dependencia para obtener la sesión de la base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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

# Modelos Pydantic
class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

class UserCreate(BaseModel):
    full_name: str
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    full_name: str
    email: str

class PortfolioResponse(BaseModel):
    id: int
    description: str
    languages: str
    type_technologies: str
    cv: str
    image_url: str
    social_networks: list
    projects: list

class SocialNetworkCreate(BaseModel):
    name: str
    url: str

class ProjectCreate(BaseModel):
    name: str
    description: str
    language_used: str
    image: UploadFile

# Ruta para registrar un usuario
@app.post("/register", response_model=UserResponse)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    logging.info("Intentando registrar un nuevo usuario")
    
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        logging.warning("El usuario ya existe")
        raise HTTPException(status_code=400, detail="El usuario ya existe")

    hashed_password = pwd_context.hash(user_data.password)
    new_user = User(
        full_name=user_data.full_name,
        email=user_data.email,
        hashed_password=hashed_password
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    logging.info("Usuario registrado exitosamente")
    
    return UserResponse(id=new_user.id, full_name=new_user.full_name, email=new_user.email)

# Ruta para login y generación de token
@app.post("/login", response_model=TokenResponse)
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    logging.info("Intentando iniciar sesión")
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        logging.warning("Credenciales incorrectas")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales incorrectas")

    token = create_jwt_token(user.id)
    logging.info("Sesión iniciada exitosamente")
    return {"access_token": token, "token_type": "bearer"}

# Ruta para crear un portafolio
@app.post("/create_portfolio/")
async def create_portfolio(
    description: str = Form(...),  # Descripción del portafolio
    languages: str = Form(...),  # Lenguajes
    type_technologies: str = Form(...),  # Tecnologías
    social_networks: str = Form(...),  # Redes sociales como texto
    cv: UploadFile = File(...),  # Subir archivo CV
    image: UploadFile = File(...),  # Subir imagen
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    logging.info("Intentando crear un nuevo portafolio")

    # Guardamos el CV en un directorio y almacenamos la ruta
    cv_directory = "static/cvs"
    os.makedirs(cv_directory, exist_ok=True)
    cv_path = os.path.join(cv_directory, cv.filename)
    with open(cv_path, "wb") as f:
        f.write(await cv.read())

    # Guardamos la imagen del proyecto
    project_directory = "static/projects"
    os.makedirs(project_directory, exist_ok=True)
    image_path = os.path.join(project_directory, image.filename)
    with open(image_path, "wb") as f:
        f.write(await image.read())

    # Crear el portafolio con la información proporcionada
    new_portfolio = Portfolio(
        user_id=current_user.id,
        description=description,
        languages=languages,
        type_technologies=type_technologies,
        cv=cv_path,  # Guardamos la ruta del archivo CV
        image_url=image_path  # Guardamos la ruta de la imagen
    )
    
    db.add(new_portfolio)
    db.commit()
    db.refresh(new_portfolio)

    # Guardamos las redes sociales
    social_network_list = social_networks.split(",")  # Asumiendo que las redes sociales se pasan como texto separado por comas
    for sn in social_network_list:
        name, url = sn.split(":")  # Asumimos que el formato es 'nombre:red_social'
        social_network = SocialNetwork(
            portfolio_id=new_portfolio.id,
            name=name.strip(),
            url=url.strip()
        )
        db.add(social_network)

    db.commit()

    logging.info("Portafolio creado exitosamente")

    return {"message": "Portafolio creado exitosamente", "portfolio_id": new_portfolio.id}

# Ruta para obtener el portafolio
@app.get("/portfolio", response_model=PortfolioResponse)
def get_portfolio(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    logging.info(f"Obteniendo portafolio del usuario {current_user.id}")
    
    portfolio = db.query(Portfolio).filter(Portfolio.user_id == current_user.id).first()
    
    if not portfolio:
        logging.warning("Portafolio no encontrado")
        raise HTTPException(status_code=404, detail="Portafolio no encontrado")
    
    social_networks = db.query(SocialNetwork).filter(SocialNetwork.portfolio_id == portfolio.id).all()
    projects = db.query(Project).filter(Project.portfolio_id == portfolio.id).all()

    return PortfolioResponse(
        id=portfolio.id,
        description=portfolio.description,
        languages=portfolio.languages,
        type_technologies=portfolio.type_technologies,
        cv=portfolio.cv,
        image_url=portfolio.image_url,
        social_networks=[{"name": sn.name, "url": sn.url} for sn in social_networks],
        projects=[{"name": project.name, "description": project.description, "image_url": project.image} for project in projects]
    )
