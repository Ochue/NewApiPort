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
    languages: List[str]  # Ahora manejamos múltiples lenguajes como lista
    projects: List[ProjectCreate]  # Lista de proyectos
    socials: List[SocialMediaCreate]  # Redes sociales (nombres y URLs)
    cv: str  # Campo para recibir el CV en Base64
    type_technologies: str  # Tecnologías utilizadas, como Web, Mobile, etc.

# Para la respuesta del portafolio
class ProjectOut(BaseModel):
    name: str
    description: str
    language: str
    image: str  # Imagen del proyecto

class SocialMediaOut(BaseModel):
    name: str
    url: str

class PortfolioOut(BaseModel):
    id: int
    full_name: str
    description: str
    languages: str  # Esto sigue siendo un campo de texto
    cv: str
    type_technologies: str
    projects: List[ProjectOut]
    socials: List[SocialMediaOut]  # Redes sociales

    class Config:
        orm_mode = True  # Habilita el modo ORM para serializar correctamente

# Para la solicitud de login
class LoginRequest(BaseModel):
    email: str
    password: str
