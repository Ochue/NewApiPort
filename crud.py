from sqlalchemy.orm import Session
from models import User, Portfolio, Project, SocialLink
from schemas import UserCreate, PortfolioCreate, ProjectCreate, SocialLinkCreate
from fastapi import UploadFile
import shutil
import os
from passlib.context import CryptContext

# Configuración para encriptar las contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def save_file(file: UploadFile, folder: str):
    file_path = f"{UPLOAD_DIR}/{folder}/{file.filename}"
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return file_path

# Función para encriptar la contraseña
def hash_password(password: str):
    return pwd_context.hash(password)

# Función para verificar la contraseña
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_user(db: Session, user: UserCreate):
    hashed_password = hash_password(user.password)
    db_user = User(email=user.email, password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def create_portfolio(db: Session, data: PortfolioCreate, cv_file: UploadFile, user_id: int):
    cv_path = save_file(cv_file, "cv")

    new_portfolio = Portfolio(
        full_name=data.full_name,
        description=data.description,
        languages=",".join(data.languages),
        cv_file=cv_path,
        user_id=user_id
    )

    db.add(new_portfolio)
    db.commit()
    db.refresh(new_portfolio)
    return new_portfolio

def create_project(db: Session, portfolio_id: int, project_data: ProjectCreate, image_file: UploadFile):
    image_path = save_file(image_file, f"projects/{portfolio_id}")

    new_project = Project(
        portfolio_id=portfolio_id,
        name=project_data.name,
        description=project_data.description,
        programming_language=project_data.programming_language,
        image_file=image_path
    )

    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    return new_project

def create_social_link(db: Session, portfolio_id: int, link_data: SocialLinkCreate):
    new_link = SocialLink(
        portfolio_id=portfolio_id,
        platform=link_data.platform,
        url=link_data.url
    )

    db.add(new_link)
    db.commit()
    db.refresh(new_link)
    return new_link
