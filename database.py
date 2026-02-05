import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# 1. Configuración de la URL (Postgres en Railway / SQLite en Local)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./vidartcamp.db")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# 2. Argumentos de conexión (necesarios para SQLite, ignorados en Postgres)
connect_args = {}
if "sqlite" in DATABASE_URL:
    connect_args = {"check_same_thread": False}

# 3. Crear el motor
engine = create_engine(
    DATABASE_URL, 
    connect_args=connect_args
)

# 4. Sesión y Base
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- ESTA ES LA FUNCIÓN QUE FALTABA ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()