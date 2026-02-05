"""
Script de administración completo para Vidartcamp V2
Ejecutar: python admin_cli.py [comando]
"""

import sys
from datetime import date, time as dt_time, datetime
from database import SessionLocal
from models import Usuario, Torneo, Equipo, Jugador, Partido
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def menu_principal():
    print("\n" + "="*60)
    print("VIDARTCAMP - ADMINISTRACIÓN")
    print("="*60)
    print("1. Gestión de Torneos")
    print("2. Gestión de Equipos")
    print("3. Gestión de Jugadores")
    print("4. Gestión de Fixture")
    print("5. Cargar Resultados")
    print("6. Ver Tabla de Posiciones")
    print("7. Usuarios Administradores")
    print("0. Salir")
    print("="*60)

# ==================== TORNEOS ====================

def listar_torneos():
    db = SessionLocal()
    torneos = db.query(Torneo).all()
    
    print("\n📋 TORNEOS:")
    print("-" * 80)
    for t in torneos:
        estado = "🟢 ACTIVO" if t.activo else "⚪ Inactivo"
        publico = "👁️  Público" if t.mostrar_publico else "🔒 Privado"
        print(f"{t.id:3d} | {t.nombre:30s} | {estado} | {publico} | {t.fecha_inicio}")
    print("-" * 80)
    db.close()

def crear_torneo():
    print("\n➕ CREAR NUEVO TORNEO")
    nombre = input("Nombre del torneo: ")
    descripcion = input("Descripción: ")
    
    print("\nFecha de inicio (YYYY-MM-DD):")
    fecha_str = input("Ejemplo: 2025-02-01: ")
    fecha_inicio = date.fromisoformat(fecha_str) if fecha_str else date.today()
    
    activo = input("¿Activar torneo ahora? (S/N): ").upper() == "S"
    mostrar_publico = input("¿Mostrar públicamente? (S/N): ").upper() == "S"
    
    db = SessionLocal()
    
    # Si se activa, desactivar otros
    if activo:
        db.query(Torneo).update({"activo": False})
    
    torneo = Torneo(
        nombre=nombre,
        descripcion=descripcion,
        fecha_inicio=fecha_inicio,
        activo=activo,
        mostrar_publico=mostrar_publico
    )
    db.add(torneo)
    db.commit()
    db.refresh(torneo)
    
    print(f"\n✅ Torneo '{nombre}' creado con ID {torneo.id}")
    db.close()

def activar_torneo():
    listar_torneos()
    torneo_id = int(input("\nID del torneo a activar: "))
    
    db = SessionLocal()
    # Desactivar todos
    db.query(Torneo).update({"activo": False})
    # Activar el seleccionado
    torneo = db.query(Torneo).filter(Torneo.id == torneo_id).first()
    if torneo:
        torneo.activo = True
        db.commit()
        print(f"✅ Torneo '{torneo.nombre}' activado")
    else:
        print("❌ Torneo no encontrado")
    db.close()

# ==================== EQUIPOS ====================

def listar_equipos():
    db = SessionLocal()
    equipos = db.query(Equipo).all()
    
    print("\n👥 EQUIPOS:")
    print("-" * 90)
    for e in equipos:
        torneo_nombre = e.torneo.nombre if e.torneo else "SIN TORNEO (Externo)"
        estado = "✅" if e.activo else "❌"
        print(f"{e.id:3d} | {e.nombre:25s} | {torneo_nombre:30s} | {estado} | Pts: {e.puntos}")
    print("-" * 90)
    db.close()

def crear_equipo():
    print("\n➕ CREAR NUEVO EQUIPO")
    db = SessionLocal()
    
    nombre = input("Nombre del equipo: ")
    
    print("\n¿Este equipo participa en un torneo?")
    print("S = Sí, participará en el torneo")
    print("N = No, es un equipo externo (solo para acceso)")
    en_torneo = input("Opción (S/N): ").upper() == "S"
    
    torneo_id = None
    if en_torneo:
        torneos = db.query(Torneo).filter(Torneo.activo == True).all()
        if not torneos:
            print("⚠️  No hay torneos activos. Crear torneo primero.")
            db.close()
            return
        
        print("\nTorneos disponibles:")
        for t in torneos:
            print(f"  {t.id}. {t.nombre}")
        torneo_id = int(input("ID del torneo: "))
    
    equipo = Equipo(
        nombre=nombre,
        torneo_id=torneo_id,
        activo=True
    )
    db.add(equipo)
    db.commit()
    db.refresh(equipo)
    
    tipo = "torneo" if torneo_id else "externo"
    print(f"✅ Equipo '{nombre}' creado como equipo {tipo} con ID {equipo.id}")
    db.close()

# ==================== JUGADORES ====================

def listar_jugadores():
    db = SessionLocal()
    jugadores = db.query(Jugador).all()
    
    print("\n👤 JUGADORES:")
    print("-" * 90)
    for j in jugadores:
        estado = "✅" if j.activo else "❌"
        print(f"{j.id:3d} | DNI: {j.dni:10s} | {j.nombre_completo:30s} | {j.equipo.nombre:20s} | {estado}")
    print("-" * 90)
    db.close()

def crear_jugador():
    print("\n➕ AGREGAR NUEVO JUGADOR")
    db = SessionLocal()
    
    # Listar equipos
    equipos = db.query(Equipo).filter(Equipo.activo == True).all()
    print("\nEquipos disponibles:")
    for e in equipos:
        torneo = f"({e.torneo.nombre})" if e.torneo else "(Externo)"
        print(f"  {e.id:3d}. {e.nombre} {torneo}")
    
    dni = input("\nDNI del jugador: ")
    nombre = input("Nombre completo: ")
    password = input("Contraseña (dejar vacío para usar DNI): ")
    if not password:
        password = dni
    equipo_id = int(input("ID del equipo: "))
    telefono = input("Teléfono (opcional): ")
    email = input("Email (opcional): ")
    
    # Verificar DNI único
    existe = db.query(Jugador).filter(Jugador.dni == dni).first()
    if existe:
        print(f"❌ Ya existe un jugador con DNI {dni}")
        db.close()
        return
    
    jugador = Jugador(
        dni=dni,
        nombre_completo=nombre,
        password_hash=pwd_context.hash(password),
        equipo_id=equipo_id,
        telefono=telefono if telefono else None,
        email=email if email else None,
        activo=True
    )
    db.add(jugador)
    db.commit()
    db.refresh(jugador)
    
    print(f"\n✅ Jugador '{nombre}' agregado con ID {jugador.id}")
    print(f"   Login: DNI {dni} / Password: {'(el ingresado)' if password != dni else dni}")
    db.close()

def cargar_jugadores_masivo():
    print("\n📥 CARGA MASIVA DE JUGADORES")
    print("Formato: DNI,Nombre Completo,ID_Equipo,Telefono,Email")
    print("Ejemplo: 12345678,Juan Pérez,1,3515555555,juan@email.com")
    print("(Presiona Enter dos veces cuando termines)")
    
    jugadores_data = []
    while True:
        linea = input()
        if not linea:
            break
        jugadores_data.append(linea)
    
    if not jugadores_data:
        print("❌ No se ingresaron datos")
        return
    
    db = SessionLocal()
    agregados = 0
    
    for linea in jugadores_data:
        try:
            partes = linea.split(",")
            dni = partes[0].strip()
            nombre = partes[1].strip()
            equipo_id = int(partes[2].strip())
            telefono = partes[3].strip() if len(partes) > 3 else None
            email = partes[4].strip() if len(partes) > 4 else None
            
            # Verificar si ya existe
            if db.query(Jugador).filter(Jugador.dni == dni).first():
                print(f"⚠️  DNI {dni} ya existe, omitiendo...")
                continue
            
            jugador = Jugador(
                dni=dni,
                nombre_completo=nombre,
                password_hash=pwd_context.hash(dni),  # Password = DNI por defecto
                equipo_id=equipo_id,
                telefono=telefono,
                email=email,
                activo=True
            )
            db.add(jugador)
            agregados += 1
            print(f"✅ {nombre} (DNI: {dni})")
        except Exception as e:
            print(f"❌ Error en línea '{linea}': {e}")
    
    db.commit()
    print(f"\n✅ {agregados} jugadores agregados")
    print("⚠️  Contraseñas = DNI por defecto")
    db.close()

# ==================== FIXTURE ====================

def listar_partidos():
    db = SessionLocal()
    
    torneo_activo = db.query(Torneo).filter(Torneo.activo == True).first()
    if not torneo_activo:
        print("❌ No hay torneo activo")
        db.close()
        return
    
    partidos = db.query(Partido).filter(
        Partido.torneo_id == torneo_activo.id
    ).order_by(Partido.jornada, Partido.fecha).all()
    
    print(f"\n⚽ FIXTURE - {torneo_activo.nombre}")
    print("-" * 100)
    
    jornada_actual = None
    for p in partidos:
        if p.jornada != jornada_actual:
            jornada_actual = p.jornada
            print(f"\n--- JORNADA {jornada_actual} ---")
        
        estado = "✅ Finalizado" if p.finalizado else "⏳ Pendiente"
        resultado = f"{p.goles_local}-{p.goles_visitante}" if p.finalizado else "vs"
        
        print(f"{p.id:3d} | {p.fecha} {p.hora.strftime('%H:%M')} | {p.equipo_local.nombre:20s} {resultado:5s} {p.equipo_visitante.nombre:20s} | {estado}")
    
    print("-" * 100)
    db.close()

def crear_partido():
    print("\n➕ CREAR NUEVO PARTIDO")
    db = SessionLocal()
    
    torneo_activo = db.query(Torneo).filter(Torneo.activo == True).first()
    if not torneo_activo:
        print("❌ No hay torneo activo")
        db.close()
        return
    
    print(f"Torneo: {torneo_activo.nombre}")
    
    # Listar equipos del torneo
    equipos = db.query(Equipo).filter(
        Equipo.torneo_id == torneo_activo.id,
        Equipo.activo == True
    ).all()
    
    print("\nEquipos disponibles:")
    for e in equipos:
        print(f"  {e.id}. {e.nombre}")
    
    local_id = int(input("\nID equipo local: "))
    visitante_id = int(input("ID equipo visitante: "))
    
    if local_id == visitante_id:
        print("❌ No puede jugar contra sí mismo")
        db.close()
        return
    
    jornada = int(input("Número de jornada: "))
    
    print("\nFecha del partido (YYYY-MM-DD):")
    fecha_str = input("Ejemplo: 2025-02-10: ")
    fecha_partido = date.fromisoformat(fecha_str)
    
    print("\nHora del partido (HH:MM):")
    hora_str = input("Ejemplo: 18:00: ")
    hora, minuto = map(int, hora_str.split(":"))
    hora_partido = dt_time(hora, minuto)
    
    cancha = input("Cancha (opcional): ")
    
    partido = Partido(
        torneo_id=torneo_activo.id,
        equipo_local_id=local_id,
        equipo_visitante_id=visitante_id,
        fecha=fecha_partido,
        hora=hora_partido,
        jornada=jornada,
        cancha=cancha if cancha else None,
        finalizado=False
    )
    db.add(partido)
    db.commit()
    db.refresh(partido)
    
    print(f"✅ Partido creado con ID {partido.id}")
    db.close()

def cargar_fixture_completo():
    print("\n📥 CARGA COMPLETA DE FIXTURE")
    print("Formato: Jornada,Local_ID,Visitante_ID,Fecha,Hora,Cancha")
    print("Ejemplo: 1,1,2,2025-02-10,18:00,Cancha 1")
    print("(Presiona Enter dos veces cuando termines)")
    
    fixture_data = []
    while True:
        linea = input()
        if not linea:
            break
        fixture_data.append(linea)
    
    if not fixture_data:
        print("❌ No se ingresaron datos")
        return
    
    db = SessionLocal()
    torneo_activo = db.query(Torneo).filter(Torneo.activo == True).first()
    if not torneo_activo:
        print("❌ No hay torneo activo")
        db.close()
        return
    
    agregados = 0
    for linea in fixture_data:
        try:
            partes = linea.split(",")
            jornada = int(partes[0].strip())
            local_id = int(partes[1].strip())
            visitante_id = int(partes[2].strip())
            fecha = date.fromisoformat(partes[3].strip())
            hora_str = partes[4].strip()
            h, m = map(int, hora_str.split(":"))
            hora = dt_time(h, m)
            cancha = partes[5].strip() if len(partes) > 5 else None
            
            partido = Partido(
                torneo_id=torneo_activo.id,
                equipo_local_id=local_id,
                equipo_visitante_id=visitante_id,
                fecha=fecha,
                hora=hora,
                jornada=jornada,
                cancha=cancha,
                finalizado=False
            )
            db.add(partido)
            agregados += 1
            
            local = db.query(Equipo).get(local_id)
            visitante = db.query(Equipo).get(visitante_id)
            print(f"✅ J{jornada}: {local.nombre} vs {visitante.nombre}")
        except Exception as e:
            print(f"❌ Error en línea '{linea}': {e}")
    
    db.commit()
    print(f"\n✅ {agregados} partidos agregados al fixture")
    db.close()

# ==================== RESULTADOS ====================

def cargar_resultado():
    print("\n📊 CARGAR RESULTADO DE PARTIDO")
    db = SessionLocal()
    
    listar_partidos()
    
    partido_id = int(input("\nID del partido: "))
    partido = db.query(Partido).filter(Partido.id == partido_id).first()
    
    if not partido:
        print("❌ Partido no encontrado")
        db.close()
        return
    
    if partido.finalizado:
        print(f"⚠️  Este partido ya está finalizado ({partido.goles_local}-{partido.goles_visitante})")
        modificar = input("¿Modificar resultado? (S/N): ").upper() == "S"
        if not modificar:
            db.close()
            return
        # Revertir estadísticas anteriores
        revertir_estadisticas(db, partido)
    
    print(f"\n{partido.equipo_local.nombre} vs {partido.equipo_visitante.nombre}")
    goles_local = int(input(f"Goles {partido.equipo_local.nombre}: "))
    goles_visitante = int(input(f"Goles {partido.equipo_visitante.nombre}: "))
    
    # Actualizar partido
    partido.goles_local = goles_local
    partido.goles_visitante = goles_visitante
    partido.finalizado = True
    
    # Actualizar estadísticas
    actualizar_estadisticas(db, partido)
    
    db.commit()
    print(f"✅ Resultado cargado: {goles_local}-{goles_visitante}")
    print("📊 Tabla de posiciones actualizada")
    db.close()

def revertir_estadisticas(db, partido):
    """Revierte las estadísticas de un partido ya cargado"""
    local = db.query(Equipo).get(partido.equipo_local_id)
    visitante = db.query(Equipo).get(partido.equipo_visitante_id)
    
    local.partidos_jugados -= 1
    local.goles_favor -= partido.goles_local
    local.goles_contra -= partido.goles_visitante
    visitante.partidos_jugados -= 1
    visitante.goles_favor -= partido.goles_visitante
    visitante.goles_contra -= partido.goles_local
    
    if partido.goles_local > partido.goles_visitante:
        local.partidos_ganados -= 1
        local.puntos -= 3
        visitante.partidos_perdidos -= 1
    elif partido.goles_local < partido.goles_visitante:
        visitante.partidos_ganados -= 1
        visitante.puntos -= 3
        local.partidos_perdidos -= 1
    else:
        local.partidos_empatados -= 1
        local.puntos -= 1
        visitante.partidos_empatados -= 1
        visitante.puntos -= 1

def actualizar_estadisticas(db, partido):
    """Actualiza las estadísticas de los equipos"""
    local = db.query(Equipo).get(partido.equipo_local_id)
    visitante = db.query(Equipo).get(partido.equipo_visitante_id)
    
    # Actualizar estadísticas generales
    local.partidos_jugados += 1
    local.goles_favor += partido.goles_local
    local.goles_contra += partido.goles_visitante
    
    visitante.partidos_jugados += 1
    visitante.goles_favor += partido.goles_visitante
    visitante.goles_contra += partido.goles_local
    
    # Determinar ganador y actualizar puntos
    if partido.goles_local > partido.goles_visitante:
        # Victoria local
        local.partidos_ganados += 1
        local.puntos += 3
        visitante.partidos_perdidos += 1
    elif partido.goles_local < partido.goles_visitante:
        # Victoria visitante
        visitante.partidos_ganados += 1
        visitante.puntos += 3
        local.partidos_perdidos += 1
    else:
        # Empate
        local.partidos_empatados += 1
        local.puntos += 1
        visitante.partidos_empatados += 1
        visitante.puntos += 1

# ==================== TABLA ====================

def ver_tabla():
    db = SessionLocal()
    
    torneo_activo = db.query(Torneo).filter(Torneo.activo == True).first()
    if not torneo_activo:
        print("❌ No hay torneo activo")
        db.close()
        return
    
    equipos = db.query(Equipo).filter(
        Equipo.torneo_id == torneo_activo.id,
        Equipo.activo == True
    ).order_by(
        Equipo.puntos.desc(),
        (Equipo.goles_favor - Equipo.goles_contra).desc(),
        Equipo.goles_favor.desc()
    ).all()
    
    print(f"\n📊 TABLA DE POSICIONES - {torneo_activo.nombre}")
    print("-" * 95)
    print(f"{'Pos':<4} {'Equipo':<25} {'PJ':<4} {'PG':<4} {'PE':<4} {'PP':<4} {'GF':<4} {'GC':<4} {'DG':<5} {'Pts':<4}")
    print("-" * 95)
    
    for idx, e in enumerate(equipos, 1):
        dg = e.goles_favor - e.goles_contra
        dg_str = f"+{dg}" if dg > 0 else str(dg)
        print(f"{idx:<4} {e.nombre:<25} {e.partidos_jugados:<4} {e.partidos_ganados:<4} {e.partidos_empatados:<4} {e.partidos_perdidos:<4} {e.goles_favor:<4} {e.goles_contra:<4} {dg_str:<5} {e.puntos:<4}")
    
    print("-" * 95)
    db.close()

# ==================== USUARIOS ADMIN ====================

def crear_admin():
    print("\n➕ CREAR USUARIO ADMINISTRADOR")
    db = SessionLocal()
    
    username = input("Username: ")
    email = input("Email: ")
    password = input("Contraseña: ")
    
    if db.query(Usuario).filter(Usuario.username == username).first():
        print(f"❌ Ya existe un usuario con username '{username}'")
        db.close()
        return
    
    usuario = Usuario(
        username=username,
        email=email,
        password_hash=pwd_context.hash(password),
        es_admin=True,
        activo=True,
        fecha_creacion=datetime.utcnow()
    )
    db.add(usuario)
    db.commit()
    
    print(f"✅ Usuario administrador '{username}' creado")
    db.close()

# ==================== MAIN ====================

def main():
    while True:
        menu_principal()
        opcion = input("\nSelecciona una opción: ")
        
        if opcion == "1":
            # Torneos
            print("\n1. Listar torneos")
            print("2. Crear torneo")
            print("3. Activar torneo")
            sub = input("Opción: ")
            if sub == "1":
                listar_torneos()
            elif sub == "2":
                crear_torneo()
            elif sub == "3":
                activar_torneo()
        
        elif opcion == "2":
            # Equipos
            print("\n1. Listar equipos")
            print("2. Crear equipo")
            sub = input("Opción: ")
            if sub == "1":
                listar_equipos()
            elif sub == "2":
                crear_equipo()
        
        elif opcion == "3":
            # Jugadores
            print("\n1. Listar jugadores")
            print("2. Agregar jugador")
            print("3. Carga masiva")
            sub = input("Opción: ")
            if sub == "1":
                listar_jugadores()
            elif sub == "2":
                crear_jugador()
            elif sub == "3":
                cargar_jugadores_masivo()
        
        elif opcion == "4":
            # Fixture
            print("\n1. Ver fixture")
            print("2. Crear partido")
            print("3. Cargar fixture completo")
            sub = input("Opción: ")
            if sub == "1":
                listar_partidos()
            elif sub == "2":
                crear_partido()
            elif sub == "3":
                cargar_fixture_completo()
        
        elif opcion == "5":
            # Resultados
            cargar_resultado()
        
        elif opcion == "6":
            # Tabla
            ver_tabla()
        
        elif opcion == "7":
            # Admins
            crear_admin()
        
        elif opcion == "0":
            print("\n👋 ¡Hasta luego!")
            break
        
        else:
            print("❌ Opción inválida")
        
        input("\nPresiona Enter para continuar...")

if __name__ == "__main__":
    main()
