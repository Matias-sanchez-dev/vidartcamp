import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# 1. Intentamos leer la URL de la base de datos desde las Variables de Entorno (Railway)
# Si no existe, usamos la dirección local de SQLite por defecto.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./vidartcamp.db")

# CORRECCIÓN PARA RAILWAY:
# A veces Railway devuelve la URL empezando con "postgres://", pero SQLAlchemy
# necesita que empiece con "postgresql://". Hacemos el reemplazo por seguridad.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# 2. Configuración de argumentos (args)
# SQLite necesita "check_same_thread: False", pero PostgreSQL NO lo soporta.
connect_args = {}
if "sqlite" in DATABASE_URL:
    connect_args = {"check_same_thread": False}

# 3. Crear el motor (Engine)
engine = create_engine(
    DATABASE_URL, 
    connect_args=connect_args
)

# 4. Crear la sesión y la base
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()