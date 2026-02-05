"""
Script de utilidades para gestión de la base de datos
Ejecutar: python db_utils.py [comando]

Comandos disponibles:
- init: Inicializar base de datos con datos de prueba
- reset: Borrar y recrear la base de datos
- add-team: Agregar un nuevo equipo
- add-player: Agregar un nuevo jugador
- add-match: Agregar un nuevo partido
- list-teams: Listar todos los equipos
- list-players: Listar todos los jugadores
- list-matches: Listar todos los partidos
- list-qr: Listar sesiones QR activas
"""

import sys
from datetime import date, time as dt_time
from database import SessionLocal, engine, Base
from models import Equipo, Jugador, Partido, SesionQR
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def init_db():
    """Inicializar base de datos con datos de prueba"""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    if db.query(Jugador).count() > 0:
        print("⚠️  La base de datos ya tiene datos. Usa 'reset' para borrar todo primero.")
        return
    
    # Crear equipos
    equipo1 = Equipo(nombre="Los Rayos", activo=True)
    equipo2 = Equipo(nombre="Los Truenos", activo=True)
    db.add_all([equipo1, equipo2])
    db.commit()
    db.refresh(equipo1)
    db.refresh(equipo2)
    
    # Crear jugadores
    jugador1 = Jugador(
        dni="123",
        nombre_completo="Juan Pérez",
        password_hash=pwd_context.hash("1234"),
        equipo_id=equipo1.id
    )
    jugador2 = Jugador(
        dni="456",
        nombre_completo="Carlos González",
        password_hash=pwd_context.hash("1234"),
        equipo_id=equipo2.id
    )
    db.add_all([jugador1, jugador2])
    db.commit()
    
    # Crear partido para HOY
    partido_hoy = Partido(
        equipo_local_id=equipo1.id,
        equipo_visitante_id=equipo2.id,
        fecha=date.today(),
        hora=dt_time(18, 0)
    )
    db.add(partido_hoy)
    db.commit()
    
    db.close()
    print("✅ Base de datos inicializada correctamente")
    print("📝 Equipos creados: Los Rayos, Los Truenos")
    print("👤 Jugadores creados: DNI 123 y 456 (password: 1234)")
    print(f"⚽ Partido creado para HOY ({date.today()}) a las 18:00")

def reset_db():
    """Borrar y recrear la base de datos"""
    print("⚠️  ADVERTENCIA: Esto borrará TODOS los datos.")
    confirm = input("¿Estás seguro? (escribe 'SI' para confirmar): ")
    if confirm != "SI":
        print("❌ Operación cancelada")
        return
    
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("✅ Base de datos reseteada")
    print("💡 Ejecuta 'python db_utils.py init' para agregar datos de prueba")

def add_team():
    """Agregar un nuevo equipo"""
    nombre = input("Nombre del equipo: ")
    activo = input("¿Activo? (S/N): ").upper() == "S"
    
    db = SessionLocal()
    equipo = Equipo(nombre=nombre, activo=activo)
    db.add(equipo)
    db.commit()
    db.refresh(equipo)
    db.close()
    
    print(f"✅ Equipo '{nombre}' creado con ID {equipo.id}")

def add_player():
    """Agregar un nuevo jugador"""
    db = SessionLocal()
    
    # Listar equipos disponibles
    equipos = db.query(Equipo).all()
    print("\n📋 Equipos disponibles:")
    for eq in equipos:
        print(f"  {eq.id}. {eq.nombre}")
    
    dni = input("\nDNI del jugador: ")
    nombre = input("Nombre completo: ")
    password = input("Contraseña: ")
    equipo_id = int(input("ID del equipo: "))
    
    jugador = Jugador(
        dni=dni,
        nombre_completo=nombre,
        password_hash=pwd_context.hash(password),
        equipo_id=equipo_id
    )
    db.add(jugador)
    db.commit()
    db.refresh(jugador)
    db.close()
    
    print(f"✅ Jugador '{nombre}' creado con ID {jugador.id}")

def add_match():
    """Agregar un nuevo partido"""
    db = SessionLocal()
    
    # Listar equipos
    equipos = db.query(Equipo).all()
    print("\n📋 Equipos disponibles:")
    for eq in equipos:
        print(f"  {eq.id}. {eq.nombre}")
    
    local_id = int(input("\nID equipo local: "))
    visitante_id = int(input("ID equipo visitante: "))
    
    print("\nFecha del partido (YYYY-MM-DD):")
    fecha_str = input("Ejemplo: 2025-02-04: ")
    año, mes, dia = map(int, fecha_str.split("-"))
    fecha_partido = date(año, mes, dia)
    
    print("\nHora del partido (HH:MM):")
    hora_str = input("Ejemplo: 18:00: ")
    hora, minuto = map(int, hora_str.split(":"))
    hora_partido = dt_time(hora, minuto)
    
    partido = Partido(
        equipo_local_id=local_id,
        equipo_visitante_id=visitante_id,
        fecha=fecha_partido,
        hora=hora_partido
    )
    db.add(partido)
    db.commit()
    db.refresh(partido)
    db.close()
    
    print(f"✅ Partido creado con ID {partido.id}")

def list_teams():
    """Listar todos los equipos"""
    db = SessionLocal()
    equipos = db.query(Equipo).all()
    
    print("\n📋 EQUIPOS:")
    print("-" * 50)
    for eq in equipos:
        estado = "✅ Activo" if eq.activo else "❌ Inactivo"
        print(f"ID: {eq.id} | {eq.nombre} | {estado}")
    print("-" * 50)
    db.close()

def list_players():
    """Listar todos los jugadores"""
    db = SessionLocal()
    jugadores = db.query(Jugador).all()
    
    print("\n👥 JUGADORES:")
    print("-" * 70)
    for j in jugadores:
        equipo = db.query(Equipo).filter(Equipo.id == j.equipo_id).first()
        print(f"ID: {j.id} | DNI: {j.dni} | {j.nombre_completo} | Equipo: {equipo.nombre}")
    print("-" * 70)
    db.close()

def list_matches():
    """Listar todos los partidos"""
    db = SessionLocal()
    partidos = db.query(Partido).all()
    
    print("\n⚽ PARTIDOS:")
    print("-" * 80)
    for p in partidos:
        local = db.query(Equipo).filter(Equipo.id == p.equipo_local_id).first()
        visitante = db.query(Equipo).filter(Equipo.id == p.equipo_visitante_id).first()
        print(f"ID: {p.id} | {p.fecha} {p.hora} | {local.nombre} vs {visitante.nombre}")
    print("-" * 80)
    db.close()

def list_qr_sessions():
    """Listar sesiones QR activas"""
    db = SessionLocal()
    sesiones = db.query(SesionQR).all()
    
    print("\n🎫 SESIONES QR:")
    print("-" * 90)
    for s in sesiones:
        jugador = db.query(Jugador).filter(Jugador.id == s.jugador_id).first()
        estado = "✅ Válido" if not s.usado else "❌ Usado"
        print(f"Token: {s.token[:8]}... | Jugador: {jugador.nombre_completo} | Expira: {s.fecha_expiracion} | {estado}")
    print("-" * 90)
    db.close()

def main():
    comandos = {
        'init': init_db,
        'reset': reset_db,
        'add-team': add_team,
        'add-player': add_player,
        'add-match': add_match,
        'list-teams': list_teams,
        'list-players': list_players,
        'list-matches': list_matches,
        'list-qr': list_qr_sessions,
    }
    
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    comando = sys.argv[1]
    
    if comando not in comandos:
        print(f"❌ Comando '{comando}' no reconocido")
        print(__doc__)
        return
    
    comandos[comando]()

if __name__ == "__main__":
    main()
