from fastapi import FastAPI, Depends, HTTPException, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta, date, time as dt_time
from typing import Optional, List
import uuid
import urllib.parse
from sqlalchemy import desc
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from database import engine, get_db, Base
from models import Usuario, Torneo, Equipo, Jugador, Partido, SesionQR

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Vidartcamp Control de Acceso v2")

# Templates
templates = Jinja2Templates(directory="templates")

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = "vidartcamp-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480
QR_EXPIRATION_SECONDS = 120

PORTERO_USERNAME = "portero"


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user(request: Request, db: Session = Depends(get_db)):
    """Get current logged user (jugador)"""
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        dni: str = payload.get("sub")
        user_type: str = payload.get("type", "jugador")
        if dni is None:
            return None
    except JWTError:
        return None
    
    if user_type == "jugador":
        jugador = db.query(Jugador).filter(Jugador.dni == dni).first()
        return jugador
    return None


def get_current_admin(request: Request, db: Session = Depends(get_db)):
    """Get current admin user"""
    token = request.cookies.get("admin_token")
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_type: str = payload.get("type")
        if username is None or user_type != "admin":
            return None
    except JWTError:
        return None
    
    usuario = db.query(Usuario).filter(
        Usuario.username == username,
        Usuario.activo == True,
        Usuario.es_admin == True
    ).first()
    if not usuario:
        return None
    return usuario


def get_current_staff(request: Request, db: Session = Depends(get_db)):
    """Get current staff user (admin or portero)"""
    token = request.cookies.get("admin_token")
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_type: str = payload.get("type")
        if username is None or user_type not in {"admin", "portero"}:
            return None
    except JWTError:
        return None

    if user_type == "admin":
        return db.query(Usuario).filter(
            Usuario.username == username,
            Usuario.activo == True,
            Usuario.es_admin == True
        ).first()

    return db.query(Usuario).filter(
        Usuario.username == username,
        Usuario.activo == True,
        Usuario.es_admin == False,
        Usuario.username == PORTERO_USERNAME
    ).first()


@app.on_event("startup")
async def startup_event():
    """Initialize database with test data"""
    db = next(get_db())
    
    # Create default admin if doesn't exist
    if not db.query(Usuario).filter(Usuario.username == "admin").first():
        admin = Usuario(
            username="admin",
            email="admin@vidartcamp.com",
            password_hash=get_password_hash("admin123"),
            es_admin=True,
            activo=True,
            fecha_creacion=datetime.utcnow()
        )
        db.add(admin)
        db.commit()
        print("✅ Usuario admin creado: username='admin', password='admin123'")

    # Create default portero if doesn't exist
    if not db.query(Usuario).filter(Usuario.username == PORTERO_USERNAME).first():
        portero = Usuario(
            username=PORTERO_USERNAME,
            email="portero@vidartcamp.com",
            password_hash=get_password_hash("portero123"),
            es_admin=False,
            activo=True,
            fecha_creacion=datetime.utcnow()
        )
        db.add(portero)
        db.commit()
        print("✅ Usuario portero creado: username='portero', password='portero123'")
    
    # Create sample tournament if doesn't exist
    if db.query(Torneo).count() == 0:
        torneo = Torneo(
            nombre="Torneo Apertura 2025",
            descripcion="Torneo de fútbol 7",
            fecha_inicio=date.today(),
            activo=True,
            mostrar_publico=True
        )
        db.add(torneo)
        db.commit()
        db.refresh(torneo)
        
        # Create teams
        equipo1 = Equipo(nombre="Los Rayos", torneo_id=torneo.id, activo=True)
        equipo2 = Equipo(nombre="Los Truenos", torneo_id=torneo.id, activo=True)
        equipo_externo = Equipo(nombre="Equipo Externo", torneo_id=None, activo=True)
        db.add_all([equipo1, equipo2, equipo_externo])
        db.commit()
        db.refresh(equipo1)
        db.refresh(equipo2)
        db.refresh(equipo_externo)
        
        # Create players
        jugador1 = Jugador(
            dni="123",
            nombre_completo="Juan Pérez",
            password_hash=get_password_hash("1234"),
            equipo_id=equipo1.id,
            activo=True
        )
        jugador2 = Jugador(
            dni="456",
            nombre_completo="Carlos González",
            password_hash=get_password_hash("1234"),
            equipo_id=equipo2.id,
            activo=True
        )
        jugador3 = Jugador(
            dni="789",
            nombre_completo="Pedro Martínez",
            password_hash=get_password_hash("1234"),
            equipo_id=equipo_externo.id,
            activo=True
        )
        db.add_all([jugador1, jugador2, jugador3])
        db.commit()
        
        # Create match for today
        partido = Partido(
            torneo_id=torneo.id,
            equipo_local_id=equipo1.id,
            equipo_visitante_id=equipo2.id,
            fecha=date.today(),
            hora=dt_time(18, 0),
            jornada=1,
            cancha="Cancha 1"
        )
        db.add(partido)
        db.commit()
        
        print("✅ Base de datos inicializada con datos de prueba")
    
    # Iniciar scheduler para reset diario
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        func=reset_ya_ingreso_diario,
        trigger=CronTrigger(hour=3, minute=0),  # Todos los días a las 00:00
        id='reset_daily_access',
        name='Reset diario de ya_ingreso',
        replace_existing=True
    )
    scheduler.start()
    print("✅ Scheduler iniciado - Reset diario configurado para las 00:00")
    
    db.close()


def reset_ya_ingreso_diario():
    """Resetea el estado ya_ingreso de todos los jugadores diariamente"""
    db = next(get_db())
    try:
        cantidad = db.query(Jugador).update({Jugador.ya_ingreso: False})
        db.commit()
        print(f"✅ Reset diario ejecutado: {cantidad} jugadores reseteados a ya_ingreso=False")
    except Exception as e:
        db.rollback()
        print(f"❌ Error en reset diario: {e}")
    finally:
        db.close()


# ==================== RUTAS PÚBLICAS ====================

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    """Home page - shows active tournament info"""
    torneo_activo = db.query(Torneo).filter(Torneo.activo == True, Torneo.mostrar_publico == True).first()
    
    return templates.TemplateResponse("home.html", {
        "request": request,
        "torneo": torneo_activo
    })


@app.get("/tabla", response_class=HTMLResponse)
async def tabla_posiciones(request: Request, db: Session = Depends(get_db)):
    """Standings table (public if tournament is public; private for logged users in a tournament)"""
    torneo = db.query(Torneo).filter(Torneo.activo == True, Torneo.mostrar_publico == True).first()

    if not torneo:
        jugador = get_current_user(request, db)
        if jugador and jugador.equipo and jugador.equipo.torneo_id:
            torneo = db.query(Torneo).filter(Torneo.id == jugador.equipo.torneo_id).first()

    if not torneo:
        jugador = get_current_user(request, db)
        if jugador and (not jugador.equipo or not jugador.equipo.torneo_id):
            return templates.TemplateResponse("error.html", {
                "request": request,
                "mensaje": "Tu equipo no está asignado a ningún torneo"
            })

        return templates.TemplateResponse("error.html", {
            "request": request,
            "mensaje": "No hay torneo activo en este momento"
        })
    
    # Get teams sorted by points
    equipos = db.query(Equipo).filter(
        Equipo.torneo_id == torneo.id,
        Equipo.activo == True
    ).order_by(
        Equipo.puntos.desc(),
        desc(Equipo.goles_favor - Equipo.goles_contra),
        Equipo.goles_favor.desc()
    ).all()
    
    return templates.TemplateResponse("tabla.html", {
        "request": request,
        "torneo": torneo,
        "equipos": equipos
    })


@app.get("/fixture", response_class=HTMLResponse)
async def fixture(request: Request, db: Session = Depends(get_db)):
    """Fixture (public if tournament is public; private for logged users in a tournament)"""
    torneo = db.query(Torneo).filter(Torneo.activo == True, Torneo.mostrar_publico == True).first()

    if not torneo:
        jugador = get_current_user(request, db)
        if jugador and jugador.equipo and jugador.equipo.torneo_id:
            torneo = db.query(Torneo).filter(Torneo.id == jugador.equipo.torneo_id).first()

    if not torneo:
        jugador = get_current_user(request, db)
        if jugador and (not jugador.equipo or not jugador.equipo.torneo_id):
            return templates.TemplateResponse("error.html", {
                "request": request,
                "mensaje": "Tu equipo no está asignado a ningún torneo"
            })

        return templates.TemplateResponse("error.html", {
            "request": request,
            "mensaje": "No hay torneo activo en este momento"
        })
    
    # Get matches grouped by jornada
    partidos = db.query(Partido).filter(
        Partido.torneo_id == torneo.id
    ).order_by(Partido.jornada, Partido.fecha, Partido.hora).all()
    
    # Group by jornada
    partidos_por_jornada = {}
    for partido in partidos:
        jornada = partido.jornada or 0
        if jornada not in partidos_por_jornada:
            partidos_por_jornada[jornada] = []
        partidos_por_jornada[jornada].append(partido)
    
    return templates.TemplateResponse("fixture.html", {
        "request": request,
        "torneo": torneo,
        "partidos_por_jornada": partidos_por_jornada
    })


# ==================== JUGADOR LOGIN Y DASHBOARD ====================

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
async def login(
    request: Request,
    dni: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    jugador = db.query(Jugador).filter(Jugador.dni == dni, Jugador.activo == True).first()
    
    if not jugador or not verify_password(password, jugador.password_hash):
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "DNI o contraseña incorrectos"
        })
    
    access_token = create_access_token(data={"sub": jugador.dni, "type": "jugador"})
    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie(key="access_token", value=access_token, httponly=True, max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    return response


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    jugador = get_current_user(request, db)
    if not jugador:
        return RedirectResponse(url="/login", status_code=302)
    
    # Check if player has match today
    hoy = date.today()
    tiene_partido = db.query(Partido).filter(
        Partido.fecha == hoy,
        ((Partido.equipo_local_id == jugador.equipo_id) | (Partido.equipo_visitante_id == jugador.equipo_id))
    ).first()
    
    partido_info = None
    if tiene_partido:
        oponente_id = tiene_partido.equipo_visitante_id if tiene_partido.equipo_local_id == jugador.equipo_id else tiene_partido.equipo_local_id
        oponente = db.query(Equipo).filter(Equipo.id == oponente_id).first()
        partido_info = {
            "hora": tiene_partido.hora.strftime("%H:%M"),
            "oponente": oponente.nombre if oponente else "Desconocido",
            "cancha": tiene_partido.cancha or "Por confirmar"
        }
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "jugador": jugador,
        "tiene_partido_hoy": tiene_partido is not None,
        "partido_info": partido_info
    })


@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=302)
    # Limpiar AMBAS cookies por seguridad
    response.delete_cookie("access_token")
    response.delete_cookie("admin_token")  # Por si acaso
    return response


@app.get("/cambiar-password", response_class=HTMLResponse)
async def cambiar_password_page(request: Request, db: Session = Depends(get_db)):
    """Página para cambiar contraseña (solo jugadores logueados)"""
    jugador = get_current_user(request, db)
    if not jugador:
        return RedirectResponse(url="/login", status_code=302)
    
    return templates.TemplateResponse("cambiar_password.html", {
        "request": request,
        "jugador": jugador
    })


@app.post("/cambiar-password")
async def cambiar_password(
    request: Request,
    password_actual: str = Form(...),
    password_nueva: str = Form(...),
    password_confirmacion: str = Form(...),
    db: Session = Depends(get_db)
):
    """Procesar cambio de contraseña"""
    jugador = get_current_user(request, db)
    if not jugador:
        return RedirectResponse(url="/login", status_code=302)
    
    # Validar contraseña actual
    if not verify_password(password_actual, jugador.password_hash):
        return templates.TemplateResponse("cambiar_password.html", {
            "request": request,
            "jugador": jugador,
            "error": "La contraseña actual es incorrecta"
        })
    
    # Validar que la nueva contraseña no esté vacía
    if not password_nueva or not password_nueva.strip():
        return templates.TemplateResponse("cambiar_password.html", {
            "request": request,
            "jugador": jugador,
            "error": "La nueva contraseña no puede estar vacía"
        })
    
    # Validar que las contraseñas coincidan
    if password_nueva != password_confirmacion:
        return templates.TemplateResponse("cambiar_password.html", {
            "request": request,
            "jugador": jugador,
            "error": "Las contraseñas nuevas no coinciden"
        })
    
    # Actualizar contraseña (hasheada)
    jugador.password_hash = get_password_hash(password_nueva)
    db.commit()
    
    # Redirigir al dashboard con mensaje de éxito
    return templates.TemplateResponse("cambiar_password.html", {
        "request": request,
        "jugador": jugador,
        "ok": "✅ Contraseña cambiada exitosamente"
    })


# ==================== QR GENERATION AND VALIDATION ====================

@app.post("/api/generar-qr")
async def generar_qr(request: Request, db: Session = Depends(get_db)):
    jugador = get_current_user(request, db)
    if not jugador:
        raise HTTPException(status_code=401, detail="No autorizado")
    
    token = str(uuid.uuid4())
    expiracion = datetime.utcnow() + timedelta(seconds=QR_EXPIRATION_SECONDS)
    
    sesion = SesionQR(
        token=token,
        jugador_id=jugador.id,
        fecha_expiracion=expiracion,
        usado=False
    )
    db.add(sesion)
    db.commit()
    
    return JSONResponse(content={
        "token": token,
        "expiracion_segundos": QR_EXPIRATION_SECONDS
    })


@app.get("/scanner", response_class=HTMLResponse)
async def scanner_page(request: Request, db: Session = Depends(get_db)):
    staff = get_current_staff(request, db)
    if not staff:
        return RedirectResponse(url="/admin/login", status_code=302)
    return templates.TemplateResponse("scanner.html", {"request": request})


@app.post("/api/validar-qr")
async def validar_qr(request: Request, db: Session = Depends(get_db)):
    staff = get_current_staff(request, db)
    if not staff:
        raise HTTPException(status_code=401, detail="No autorizado")

    data = await request.json()
    token = data.get("token")
    
    if not token:
        return JSONResponse(content={"status": "error", "mensaje": "Token no proporcionado"}, status_code=400)
    
    sesion = db.query(SesionQR).filter(SesionQR.token == token).first()
    
    if not sesion:
        return JSONResponse(content={"status": "error", "mensaje": "QR no válido"})
    
    # PROTECCIÓN CONTRA DOBLE ACCESO: Verificar si el jugador ya ingresó
    jugador = db.query(Jugador).filter(Jugador.id == sesion.jugador_id).first()
    
    if jugador.ya_ingreso:
        return JSONResponse(content={
            "status": "error", 
            "mensaje": "⚠️ ESTE JUGADOR YA INGRESÓ AL PREDIO (Intento de doble acceso)"
        })
    
    if sesion.usado:
        return JSONResponse(content={"status": "error", "mensaje": "QR ya utilizado"})
    
    if datetime.utcnow() > sesion.fecha_expiracion:
        return JSONResponse(content={"status": "error", "mensaje": "QR expirado"})
    
    equipo = db.query(Equipo).filter(Equipo.id == jugador.equipo_id).first()
    
    # Marcar token como usado y jugador como ingresado
    sesion.usado = True
    sesion.fecha_uso = datetime.utcnow()
    jugador.ya_ingreso = True  # Prevenir doble acceso
    db.commit()
    
    return JSONResponse(content={
        "status": "ok",
        "nombre": jugador.nombre_completo,
        "equipo": equipo.nombre,
        "dni": jugador.dni
    })


# ==================== ADMIN ROUTES ====================

@app.get("/admin/login", response_class=HTMLResponse)
async def admin_login_page(request: Request, db: Session = Depends(get_db)):
    # Si ya tiene sesión de admin válida, redirigir al panel
    admin = get_current_admin(request, db)
    if admin:
        return RedirectResponse(url="/admin", status_code=302)
    
    # Si tiene sesión de jugador, ignorarla y mostrar login
    # (no importa que tenga access_token, debe logearse como admin)
    return templates.TemplateResponse("admin_login.html", {"request": request})


@app.post("/admin/login")
async def admin_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    usuario = db.query(Usuario).filter(
        Usuario.username == username,
        Usuario.activo == True
    ).first()
    
    if not usuario or not verify_password(password, usuario.password_hash):
        return templates.TemplateResponse("admin_login.html", {
            "request": request,
            "error": "Usuario o contraseña incorrectos"
        })

    if usuario.es_admin == True:
        access_token = create_access_token(data={"sub": usuario.username, "type": "admin"})
        response = RedirectResponse(url="/admin", status_code=302)
        response.set_cookie(key="admin_token", value=access_token, httponly=True, max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60)
        return response

    if usuario.username == PORTERO_USERNAME:
        access_token = create_access_token(data={"sub": usuario.username, "type": "portero"})
        response = RedirectResponse(url="/scanner", status_code=302)
        response.set_cookie(key="admin_token", value=access_token, httponly=True, max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60)
        return response

    return templates.TemplateResponse("admin_login.html", {
        "request": request,
        "error": "No autorizado"
    })


@app.get("/admin", response_class=HTMLResponse)
async def admin_panel(request: Request, db: Session = Depends(get_db)):
    admin = get_current_admin(request, db)
    if not admin:
        response = RedirectResponse(url="/admin/login", status_code=302)
        # Limpiar admin_token si existe
        response.delete_cookie("admin_token")
        return response

    hoy = date.today()
    total_jugadores = db.query(Jugador).filter(Jugador.activo == True).count()
    partidos_hoy = db.query(Partido).filter(Partido.fecha == hoy).count()
    total_equipos = db.query(Equipo).filter(Equipo.activo == True).count()

    torneos = db.query(Torneo).order_by(Torneo.id.desc()).all()
    
    # Calcular estadísticas para cada torneo
    torneos_con_stats = []
    for t in torneos:
        equipos_count = db.query(Equipo).filter(Equipo.torneo_id == t.id).count()
        partidos_count = db.query(Partido).filter(Partido.torneo_id == t.id).count()
        torneos_con_stats.append({
            "torneo": t,
            "equipos_count": equipos_count,
            "partidos_count": partidos_count
        })
    
    torneo_activo = db.query(Torneo).filter(Torneo.activo == True).first()

    torneo_id_raw = request.query_params.get("torneo_id")
    torneo_seleccionado = None
    if torneo_id_raw:
        try:
            torneo_id = int(torneo_id_raw)
            torneo_seleccionado = db.query(Torneo).filter(Torneo.id == torneo_id).first()
        except ValueError:
            torneo_seleccionado = None
    if not torneo_seleccionado:
        torneo_seleccionado = torneo_activo

    equipos = db.query(Equipo).filter(Equipo.activo == True).order_by(Equipo.nombre.asc()).all()
    equipos_torneo = []
    if torneo_seleccionado:
        equipos_torneo = db.query(Equipo).filter(
            Equipo.activo == True,
            Equipo.torneo_id == torneo_seleccionado.id
        ).order_by(Equipo.nombre.asc()).all()

    partidos_de_hoy = db.query(Partido).filter(Partido.fecha == hoy).order_by(Partido.hora.asc()).all()
    partidos_torneo = []
    if torneo_seleccionado:
        partidos_torneo = db.query(Partido).filter(
            Partido.torneo_id == torneo_seleccionado.id
        ).order_by(Partido.jornada, Partido.fecha, Partido.hora).all()

    equipos_con_jugadores = []
    for equipo in equipos:
        jugadores_equipo = db.query(Jugador).filter(
            Jugador.equipo_id == equipo.id,
            Jugador.activo == True
        ).order_by(Jugador.nombre_completo.asc()).all()
        equipos_con_jugadores.append({"equipo": equipo, "jugadores": jugadores_equipo})

    active_tab = request.query_params.get("tab", "dashboard")
    if active_tab not in {"dashboard", "equipos", "jugadores", "partidos", "torneos"}:
        active_tab = "dashboard"

    ok_raw = request.query_params.get("ok")
    error_raw = request.query_params.get("error")
    ok = urllib.parse.unquote(ok_raw) if ok_raw else None
    error = urllib.parse.unquote(error_raw) if error_raw else None

    return templates.TemplateResponse("admin.html", {
        "request": request,
        "admin": admin,
        "hoy": hoy,
        "torneos": torneos,
        "torneos_con_stats": torneos_con_stats,
        "torneo_activo": torneo_activo,
        "torneo_seleccionado": torneo_seleccionado,
        "total_jugadores": total_jugadores,
        "partidos_hoy": partidos_hoy,
        "total_equipos": total_equipos,
        "equipos": equipos,
        "equipos_torneo": equipos_torneo,
        "equipos_con_jugadores": equipos_con_jugadores,
        "partidos_de_hoy": partidos_de_hoy,
        "partidos_torneo": partidos_torneo,
        "active_tab": active_tab,
        "ok": ok,
        "error": error,
    })


@app.get("/admin/logout")
async def admin_logout():
    response = RedirectResponse(url="/admin/login", status_code=302)
    # Limpiar AMBAS cookies por seguridad
    response.delete_cookie("admin_token")
    response.delete_cookie("access_token")  # Por si acaso
    return response


def recalculate_torneo_positions(torneo_id: int, db: Session):
    equipos_t = db.query(Equipo).filter(Equipo.torneo_id == torneo_id, Equipo.activo == True).all()
    equipos_by_id = {e.id: e for e in equipos_t}

    for e in equipos_t:
        e.partidos_jugados = 0
        e.partidos_ganados = 0
        e.partidos_empatados = 0
        e.partidos_perdidos = 0
        e.goles_favor = 0
        e.goles_contra = 0
        e.puntos = 0

    partidos_finalizados = db.query(Partido).filter(
        Partido.torneo_id == torneo_id,
        Partido.finalizado == True,
        Partido.goles_local != None,
        Partido.goles_visitante != None
    ).all()

    for p in partidos_finalizados:
        local = equipos_by_id.get(p.equipo_local_id)
        visitante = equipos_by_id.get(p.equipo_visitante_id)
        if not local or not visitante:
            continue

        gl = int(p.goles_local)
        gv = int(p.goles_visitante)

        local.partidos_jugados += 1
        visitante.partidos_jugados += 1
        local.goles_favor += gl
        local.goles_contra += gv
        visitante.goles_favor += gv
        visitante.goles_contra += gl

        if gl > gv:
            local.partidos_ganados += 1
            visitante.partidos_perdidos += 1
            local.puntos += 3
        elif gl < gv:
            visitante.partidos_ganados += 1
            local.partidos_perdidos += 1
            visitante.puntos += 3
        else:
            local.partidos_empatados += 1
            visitante.partidos_empatados += 1
            local.puntos += 1
            visitante.puntos += 1


@app.post("/admin/torneos")
async def admin_crear_torneo(
    request: Request,
    nombre: str = Form(...),
    descripcion: Optional[str] = Form(None),
    fecha_inicio: Optional[str] = Form(None),
    fecha_fin: Optional[str] = Form(None),
    mostrar_publico: Optional[str] = Form(None),
    activar: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    admin_token = request.cookies.get("admin_token")
    user_token = request.cookies.get("access_token")
    admin = get_current_admin(request, db)
    if not admin:
        if admin_token:
            raise HTTPException(status_code=403, detail="No autorizado")
        if user_token:
            return RedirectResponse(url="/", status_code=302)
        return RedirectResponse(url="/admin/login", status_code=302)

    nombre_limpio = (nombre or "").strip()
    if not nombre_limpio:
        msg = urllib.parse.quote("Nombre de torneo inválido")
        return RedirectResponse(url=f"/admin?tab=torneos&error={msg}", status_code=302)

    fi = None
    ff = None
    try:
        if fecha_inicio:
            fi = date.fromisoformat(fecha_inicio)
        if fecha_fin:
            ff = date.fromisoformat(fecha_fin)
    except ValueError:
        msg = urllib.parse.quote("Fecha inválida")
        return RedirectResponse(url=f"/admin?tab=torneos&error={msg}", status_code=302)

    torneo = Torneo(
        nombre=nombre_limpio,
        descripcion=(descripcion or "").strip() or None,
        fecha_inicio=fi,
        fecha_fin=ff,
        activo=False,
        mostrar_publico=True if mostrar_publico else False,
    )
    db.add(torneo)
    db.commit()
    db.refresh(torneo)

    if activar:
        db.query(Torneo).update({Torneo.activo: False})
        torneo.activo = True
        db.commit()

    msg = urllib.parse.quote("Torneo creado")
    return RedirectResponse(url=f"/admin?tab=torneos&torneo_id={torneo.id}&ok={msg}", status_code=302)


@app.post("/admin/torneos/activar")
async def admin_activar_torneo(
    request: Request,
    torneo_id: int = Form(...),
    db: Session = Depends(get_db)
):
    admin_token = request.cookies.get("admin_token")
    user_token = request.cookies.get("access_token")
    admin = get_current_admin(request, db)
    if not admin:
        if admin_token:
            raise HTTPException(status_code=403, detail="No autorizado")
        if user_token:
            return RedirectResponse(url="/", status_code=302)
        return RedirectResponse(url="/admin/login", status_code=302)

    torneo = db.query(Torneo).filter(Torneo.id == torneo_id).first()
    if not torneo:
        msg = urllib.parse.quote("Torneo no encontrado")
        return RedirectResponse(url=f"/admin?tab=torneos&error={msg}", status_code=302)

    db.query(Torneo).update({Torneo.activo: False})
    torneo.activo = True
    db.commit()

    msg = urllib.parse.quote("Torneo activado")
    return RedirectResponse(url=f"/admin?tab=torneos&torneo_id={torneo.id}&ok={msg}", status_code=302)


@app.post("/admin/torneos/publico")
async def admin_toggle_torneo_publico(
    request: Request,
    torneo_id: int = Form(...),
    db: Session = Depends(get_db)
):
    admin_token = request.cookies.get("admin_token")
    user_token = request.cookies.get("access_token")
    admin = get_current_admin(request, db)
    if not admin:
        if admin_token:
            raise HTTPException(status_code=403, detail="No autorizado")
        if user_token:
            return RedirectResponse(url="/", status_code=302)
        return RedirectResponse(url="/admin/login", status_code=302)

    torneo = db.query(Torneo).filter(Torneo.id == torneo_id).first()
    if not torneo:
        msg = urllib.parse.quote("Torneo no encontrado")
        return RedirectResponse(url=f"/admin?tab=torneos&error={msg}", status_code=302)

    torneo.mostrar_publico = not bool(torneo.mostrar_publico)
    db.commit()

    msg = urllib.parse.quote("Visibilidad actualizada")
    return RedirectResponse(url=f"/admin?tab=torneos&torneo_id={torneo.id}&ok={msg}", status_code=302)


@app.post("/admin/torneos/eliminar")
async def admin_eliminar_torneo(
    request: Request,
    torneo_id: int = Form(...),
    db: Session = Depends(get_db)
):
    admin = get_current_admin(request, db)
    if not admin:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    torneo = db.query(Torneo).filter(Torneo.id == torneo_id).first()
    if not torneo:
        msg = urllib.parse.quote("Torneo no encontrado")
        return RedirectResponse(url=f"/admin?tab=torneos&error={msg}", status_code=302)
    
    # Eliminar partidos asociados
    db.query(Partido).filter(Partido.torneo_id == torneo_id).delete()
    
    # Desasignar equipos (poner torneo_id = NULL)
    db.query(Equipo).filter(Equipo.torneo_id == torneo_id).update({Equipo.torneo_id: None})
    
    # Eliminar torneo
    nombre_torneo = torneo.nombre
    db.delete(torneo)
    db.commit()
    
    msg = urllib.parse.quote(f"Torneo '{nombre_torneo}' eliminado (incluyendo partidos asociados)")
    return RedirectResponse(url=f"/admin?tab=torneos&ok={msg}", status_code=302)


@app.post("/admin/torneos/asignar-equipos")
async def admin_asignar_equipos_torneo(
    request: Request,
    torneo_id: int = Form(...),
    equipo_ids: List[int] = Form([]),
    db: Session = Depends(get_db)
):
    admin_token = request.cookies.get("admin_token")
    user_token = request.cookies.get("access_token")
    admin = get_current_admin(request, db)
    if not admin:
        if admin_token:
            raise HTTPException(status_code=403, detail="No autorizado")
        if user_token:
            return RedirectResponse(url="/", status_code=302)
        return RedirectResponse(url="/admin/login", status_code=302)

    torneo = db.query(Torneo).filter(Torneo.id == torneo_id).first()
    if not torneo:
        msg = urllib.parse.quote("Torneo no encontrado")
        return RedirectResponse(url=f"/admin?tab=torneos&error={msg}", status_code=302)

    selected_ids = set(int(x) for x in (equipo_ids or []))

    equipos_t = db.query(Equipo).filter(Equipo.activo == True).all()
    for e in equipos_t:
        if e.id in selected_ids:
            e.torneo_id = torneo.id
        elif e.torneo_id == torneo.id:
            e.torneo_id = None

    db.commit()
    recalculate_torneo_positions(torneo.id, db)
    db.commit()

    msg = urllib.parse.quote("Equipos asignados")
    return RedirectResponse(url=f"/admin?tab=torneos&torneo_id={torneo.id}&ok={msg}", status_code=302)


@app.post("/admin/equipos")
async def admin_crear_equipo(
    request: Request,
    nombre: str = Form(...),
    db: Session = Depends(get_db)
):
    admin_token = request.cookies.get("admin_token")
    user_token = request.cookies.get("access_token")
    admin = get_current_admin(request, db)
    if not admin:
        if admin_token:
            raise HTTPException(status_code=403, detail="No autorizado")
        if user_token:
            return RedirectResponse(url="/", status_code=302)
        return RedirectResponse(url="/admin/login", status_code=302)

    nombre_limpio = (nombre or "").strip()
    if not nombre_limpio:
        msg = urllib.parse.quote("Nombre de equipo inválido")
        return RedirectResponse(url=f"/admin?tab=equipos&error={msg}", status_code=302)

    existe = db.query(Equipo).filter(Equipo.nombre == nombre_limpio).first()
    if existe:
        msg = urllib.parse.quote("Ya existe un equipo con ese nombre")
        return RedirectResponse(url=f"/admin?tab=equipos&error={msg}", status_code=302)

    torneo_activo = db.query(Torneo).filter(Torneo.activo == True).first()
    equipo = Equipo(
        nombre=nombre_limpio,
        activo=True,
        torneo_id=torneo_activo.id if torneo_activo else None
    )
    db.add(equipo)
    db.commit()

    msg = urllib.parse.quote("Equipo creado")
    return RedirectResponse(url=f"/admin?tab=equipos&ok={msg}", status_code=302)


@app.post("/admin/equipos/eliminar")
async def admin_eliminar_equipo(
    request: Request,
    equipo_id: int = Form(...),
    db: Session = Depends(get_db)
):
    """Eliminar equipo y todos sus jugadores asociados"""
    admin = get_current_admin(request, db)
    if not admin:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    equipo = db.query(Equipo).filter(Equipo.id == equipo_id, Equipo.activo == True).first()
    if not equipo:
        msg = urllib.parse.quote("Equipo no encontrado")
        return RedirectResponse(url=f"/admin?tab=equipos&error={msg}", status_code=302)
    
    # Contar jugadores asociados activos
    jugadores_count = db.query(Jugador).filter(
        Jugador.equipo_id == equipo_id,
        Jugador.activo == True
    ).count()
    
    # Marcar jugadores como inactivos (soft delete)
    db.query(Jugador).filter(Jugador.equipo_id == equipo_id).update({Jugador.activo: False})
    
    # Marcar equipo como inactivo (soft delete)
    nombre_equipo = equipo.nombre
    equipo.activo = False
    db.commit()
    
    msg = urllib.parse.quote(
        f"Equipo '{nombre_equipo}' eliminado ({jugadores_count} jugador(es) también eliminado(s))"
    )
    return RedirectResponse(url=f"/admin?tab=equipos&ok={msg}", status_code=302)


@app.post("/admin/jugadores")
async def admin_crear_jugador(
    request: Request,
    nombre_completo: str = Form(...),
    dni: str = Form(...),
    equipo_id: int = Form(...),
    db: Session = Depends(get_db)
):
    admin_token = request.cookies.get("admin_token")
    user_token = request.cookies.get("access_token")
    admin = get_current_admin(request, db)
    if not admin:
        if admin_token:
            raise HTTPException(status_code=403, detail="No autorizado")
        if user_token:
            return RedirectResponse(url="/", status_code=302)
        return RedirectResponse(url="/admin/login", status_code=302)

    nombre_limpio = (nombre_completo or "").strip()
    dni_limpio = (dni or "").strip()
    if not nombre_limpio or not dni_limpio:
        msg = urllib.parse.quote("Nombre y DNI son obligatorios")
        return RedirectResponse(url=f"/admin?tab=jugadores&error={msg}", status_code=302)

    equipo = db.query(Equipo).filter(Equipo.id == equipo_id, Equipo.activo == True).first()
    if not equipo:
        msg = urllib.parse.quote("Equipo inválido")
        return RedirectResponse(url=f"/admin?tab=jugadores&error={msg}", status_code=302)

    existe = db.query(Jugador).filter(Jugador.dni == dni_limpio).first()
    if existe:
        msg = urllib.parse.quote("Ya existe un jugador con ese DNI")
        return RedirectResponse(url=f"/admin?tab=jugadores&error={msg}", status_code=302)

    jugador = Jugador(
        dni=dni_limpio,
        nombre_completo=nombre_limpio,
        password_hash=get_password_hash(dni_limpio),
        equipo_id=equipo.id,
        activo=True
    )
    db.add(jugador)
    db.commit()

    msg = urllib.parse.quote("Jugador inscripto")
    return RedirectResponse(url=f"/admin?tab=jugadores&ok={msg}", status_code=302)


@app.post("/admin/jugadores/editar")
async def admin_editar_jugador(
    request: Request,
    jugador_id: int = Form(...),
    nombre_completo: str = Form(...),
    dni: str = Form(...),
    equipo_id: int = Form(...),
    telefono: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    admin_token = request.cookies.get("admin_token")
    user_token = request.cookies.get("access_token")
    admin = get_current_admin(request, db)
    if not admin:
        if admin_token:
            raise HTTPException(status_code=403, detail="No autorizado")
        if user_token:
            return RedirectResponse(url="/", status_code=302)
        return RedirectResponse(url="/admin/login", status_code=302)

    jugador = db.query(Jugador).filter(Jugador.id == jugador_id, Jugador.activo == True).first()
    if not jugador:
        msg = urllib.parse.quote("Jugador no encontrado")
        return RedirectResponse(url=f"/admin?tab=jugadores&error={msg}", status_code=302)

    nombre_limpio = (nombre_completo or "").strip()
    dni_limpio = (dni or "").strip()
    telefono_limpio = (telefono or "").strip() or None
    email_limpio = (email or "").strip() or None

    if not nombre_limpio or not dni_limpio:
        msg = urllib.parse.quote("Nombre y DNI son obligatorios")
        return RedirectResponse(url=f"/admin?tab=jugadores&error={msg}", status_code=302)

    equipo = db.query(Equipo).filter(Equipo.id == equipo_id, Equipo.activo == True).first()
    if not equipo:
        msg = urllib.parse.quote("Equipo inválido")
        return RedirectResponse(url=f"/admin?tab=jugadores&error={msg}", status_code=302)

    if jugador.dni != dni_limpio:
        existe = db.query(Jugador).filter(Jugador.dni == dni_limpio).first()
        if existe:
            msg = urllib.parse.quote("Ya existe un jugador con ese DNI")
            return RedirectResponse(url=f"/admin?tab=jugadores&error={msg}", status_code=302)

    jugador.nombre_completo = nombre_limpio
    jugador.dni = dni_limpio
    jugador.telefono = telefono_limpio
    jugador.email = email_limpio
    jugador.equipo_id = equipo.id
    db.commit()

    msg = urllib.parse.quote("Jugador actualizado")
    return RedirectResponse(url=f"/admin?tab=jugadores&ok={msg}", status_code=302)


@app.post("/admin/jugadores/borrar")
async def admin_borrar_jugador(
    request: Request,
    jugador_id: int = Form(...),
    db: Session = Depends(get_db)
):
    admin_token = request.cookies.get("admin_token")
    user_token = request.cookies.get("access_token")
    admin = get_current_admin(request, db)
    if not admin:
        if admin_token:
            raise HTTPException(status_code=403, detail="No autorizado")
        if user_token:
            return RedirectResponse(url="/", status_code=302)
        return RedirectResponse(url="/admin/login", status_code=302)

    jugador = db.query(Jugador).filter(Jugador.id == jugador_id, Jugador.activo == True).first()
    if not jugador:
        msg = urllib.parse.quote("Jugador no encontrado")
        return RedirectResponse(url=f"/admin?tab=jugadores&error={msg}", status_code=302)

    jugador.activo = False
    db.commit()

    msg = urllib.parse.quote("Jugador eliminado de la lista")
    return RedirectResponse(url=f"/admin?tab=jugadores&ok={msg}", status_code=302)


@app.post("/admin/partidos")
async def admin_crear_partido_hoy(
    request: Request,
    torneo_id: Optional[int] = Form(None),
    fecha: Optional[str] = Form(None),
    equipo_local_id: int = Form(...),
    equipo_visitante_id: int = Form(...),
    hora: str = Form(...),
    jornada: Optional[int] = Form(None),
    cancha: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    admin_token = request.cookies.get("admin_token")
    user_token = request.cookies.get("access_token")
    admin = get_current_admin(request, db)
    if not admin:
        if admin_token:
            raise HTTPException(status_code=403, detail="No autorizado")
        if user_token:
            return RedirectResponse(url="/", status_code=302)
        return RedirectResponse(url="/admin/login", status_code=302)

    if equipo_local_id == equipo_visitante_id:
        msg = urllib.parse.quote("Local y visitante no pueden ser el mismo equipo")
        return RedirectResponse(url=f"/admin?tab=partidos&error={msg}", status_code=302)

    equipo_local = db.query(Equipo).filter(Equipo.id == equipo_local_id, Equipo.activo == True).first()
    equipo_visitante = db.query(Equipo).filter(Equipo.id == equipo_visitante_id, Equipo.activo == True).first()
    if not equipo_local or not equipo_visitante:
        msg = urllib.parse.quote("Equipos inválidos")
        return RedirectResponse(url=f"/admin?tab=partidos&error={msg}", status_code=302)

    try:
        hora_dt = dt_time.fromisoformat(hora)
    except ValueError:
        msg = urllib.parse.quote("Hora inválida (formato HH:MM)")
        return RedirectResponse(url=f"/admin?tab=partidos&error={msg}", status_code=302)

    torneo_activo = db.query(Torneo).filter(Torneo.activo == True).first()
    torneo = None
    if torneo_id is not None:
        torneo = db.query(Torneo).filter(Torneo.id == torneo_id).first()
    if torneo is None:
        torneo = torneo_activo
    if not torneo:
        msg = urllib.parse.quote("No hay torneo seleccionado")
        return RedirectResponse(url=f"/admin?tab=partidos&error={msg}", status_code=302)

    try:
        fecha_dt = date.fromisoformat(fecha) if fecha else date.today()
    except ValueError:
        msg = urllib.parse.quote("Fecha inválida")
        return RedirectResponse(url=f"/admin?tab=partidos&torneo_id={torneo.id}&error={msg}", status_code=302)

    if equipo_local.torneo_id != torneo.id or equipo_visitante.torneo_id != torneo.id:
        msg = urllib.parse.quote("Los equipos deben pertenecer al torneo seleccionado")
        return RedirectResponse(url=f"/admin?tab=partidos&torneo_id={torneo.id}&error={msg}", status_code=302)

    partido = Partido(
        torneo_id=torneo.id,
        equipo_local_id=equipo_local.id,
        equipo_visitante_id=equipo_visitante.id,
        fecha=fecha_dt,
        hora=hora_dt,
        jornada=jornada,
        cancha=(cancha or "").strip() or None,
    )
    db.add(partido)
    db.commit()

    msg = urllib.parse.quote("Partido creado")
    return RedirectResponse(url=f"/admin?tab=partidos&torneo_id={torneo.id}&ok={msg}", status_code=302)


@app.post("/admin/partidos/resultado")
async def admin_cargar_resultado(
    request: Request,
    partido_id: int = Form(...),
    goles_local: int = Form(...),
    goles_visitante: int = Form(...),
    db: Session = Depends(get_db)
):
    admin_token = request.cookies.get("admin_token")
    user_token = request.cookies.get("access_token")
    admin = get_current_admin(request, db)
    if not admin:
        if admin_token:
            raise HTTPException(status_code=403, detail="No autorizado")
        if user_token:
            return RedirectResponse(url="/", status_code=302)
        return RedirectResponse(url="/admin/login", status_code=302)

    partido = db.query(Partido).filter(Partido.id == partido_id).first()
    if not partido:
        msg = urllib.parse.quote("Partido no encontrado")
        return RedirectResponse(url=f"/admin?tab=partidos&error={msg}", status_code=302)

    partido.goles_local = int(goles_local)
    partido.goles_visitante = int(goles_visitante)
    partido.finalizado = True
    db.commit()

    if partido.torneo_id:
        recalculate_torneo_positions(partido.torneo_id, db)
        db.commit()

    msg = urllib.parse.quote("Resultado guardado")
    tid = partido.torneo_id
    torneo_qs = f"&torneo_id={tid}" if tid else ""
    return RedirectResponse(url=f"/admin?tab=partidos{torneo_qs}&ok={msg}", status_code=302)


@app.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    return RedirectResponse(url="/admin", status_code=302)


@app.get("/admin/logout")
async def admin_logout():
    response = RedirectResponse(url="/admin/login", status_code=302)
    response.delete_cookie("admin_token")
    return response


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
