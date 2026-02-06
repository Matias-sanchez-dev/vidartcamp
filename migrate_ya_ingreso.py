"""
Script de migración: Agregar columna ya_ingreso a la tabla jugadores
"""
import sqlite3
import os

# Ruta a la base de datos
DB_PATH = "vidartcamp.db"

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"✅ Base de datos '{DB_PATH}' no existe aún. La columna se creará automáticamente al iniciar la app.")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Verificar si la columna ya existe
        cursor.execute("PRAGMA table_info(jugadores)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'ya_ingreso' in columns:
            print("✅ La columna 'ya_ingreso' ya existe en la tabla jugadores")
        else:
            # Agregar la columna
            cursor.execute("ALTER TABLE jugadores ADD COLUMN ya_ingreso BOOLEAN DEFAULT 0")
            conn.commit()
            print("✅ Columna 'ya_ingreso' agregada exitosamente a la tabla jugadores")
        
    except sqlite3.Error as e:
        print(f"❌ Error durante la migración: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
