"""
Script de migración: Agregar columna ya_ingreso a la tabla jugadores
Compatible con SQLite (local) y PostgreSQL (Railway)
"""
import os
import sys

def migrate_sqlite():
    """Migración para SQLite (desarrollo local)"""
    import sqlite3
    
    DB_PATH = "vidartcamp.db"
    
    if not os.path.exists(DB_PATH):
        print(f"✅ Base de datos '{DB_PATH}' no existe aún. La columna se creará automáticamente al iniciar la app.")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("PRAGMA table_info(jugadores)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'ya_ingreso' in columns:
            print("✅ La columna 'ya_ingreso' ya existe en la tabla jugadores (SQLite)")
        else:
            cursor.execute("ALTER TABLE jugadores ADD COLUMN ya_ingreso BOOLEAN DEFAULT 0")
            conn.commit()
            print("✅ Columna 'ya_ingreso' agregada exitosamente a la tabla jugadores (SQLite)")
    except Exception as e:
        print(f"❌ Error durante la migración SQLite: {e}")
        conn.rollback()
    finally:
        conn.close()


def migrate_postgresql():
    """Migración para PostgreSQL (Railway)"""
    from sqlalchemy import create_engine, text
    
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    if not DATABASE_URL:
        print("❌ DATABASE_URL no configurada. Asegúrate de estar en Railway o tener la variable configurada.")
        return
    
    # Fix para Railway: railway usa postgres:// pero SQLAlchemy necesita postgresql://
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            # PostgreSQL soporta IF NOT EXISTS desde versión 9.6+
            conn.execute(text("""
                ALTER TABLE jugadores 
                ADD COLUMN IF NOT EXISTS ya_ingreso BOOLEAN DEFAULT false
            """))
            conn.commit()
            print("✅ Columna 'ya_ingreso' agregada/verificada en PostgreSQL")
    except Exception as e:
        print(f"❌ Error durante la migración PostgreSQL: {e}")
    finally:
        engine.dispose()


if __name__ == "__main__":
    # Detectar automáticamente si estamos en Railway (PostgreSQL) o local (SQLite)
    if os.getenv("DATABASE_URL"):
        print("🔍 Detectado PostgreSQL (Railway)")
        migrate_postgresql()
    else:
        print("🔍 Detectado SQLite (local)")
        migrate_sqlite()
