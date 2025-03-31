from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    
    portfolios = relationship("Portfolio", back_populates="owner")

class Portfolio(Base):
    __tablename__ = "portfolios"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    description = Column(String)
    languages = Column(String)
    cv = Column(String)

    owner = relationship("User", back_populates="portfolios")
    projects = relationship("Project", back_populates="portfolio")
    socials = relationship("SocialMedia", back_populates="portfolio")

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"))
    name = Column(String)
    description = Column(String)
    language = Column(String)
    image = Column(String)

    portfolio = relationship("Portfolio", back_populates="projects")

class SocialMedia(Base):
    __tablename__ = "social_media"
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"))
    name = Column(String)
    url = Column(String)

    portfolio = relationship("Portfolio", back_populates="socials")
