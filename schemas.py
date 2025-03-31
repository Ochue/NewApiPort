from pydantic import BaseModel
from typing import List

# Para la creación de un usuario
class UserCreate(BaseModel):
    full_name: str
    email: str
    password: str  # Aquí la contraseña debe ser en texto plano, en producción deberías encriptarla

class UserOut(BaseModel):
    id: int
    full_name: str
    email: str

    class Config:
        orm_mode = True  # Configuración para usar objetos ORM

# Para la creación del portafolio
class ProjectCreate(BaseModel):
    name: str
    description: str
    language: str
    image_base64: str  # Este campo será la imagen en Base64

class SocialMediaCreate(BaseModel):
    name: str
    url: str

class PortfolioCreate(BaseModel):
    full_name: str
    description: str
    languages: str
    projects: List[ProjectCreate]
    socials: List[dict]
    cv: str  # Campo para recibir el CV en Base64

# Para la respuesta del portafolio
class ProjectOut(BaseModel):
    name: str
    description: str
    language: str
    image: str

class SocialMediaOut(BaseModel):
    name: str
    url: str

class PortfolioOut(BaseModel):  # Esto es lo que te faltaba definir
    id: int
    full_name: str
    description: str
    languages: str
    cv: str
    projects: List[ProjectOut]
    socials: List[SocialMediaOut]

    class Config:
        orm_mode = True


# Para la solicitud de login
class LoginRequest(BaseModel):
    email: str
    password: str