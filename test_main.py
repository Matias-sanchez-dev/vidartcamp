"""
Tests básicos para el sistema Vidartcamp
Ejecutar: pytest test_main.py -v
"""

import pytest
from fastapi.testclient import TestClient
from datetime import date, time as dt_time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app, get_current_user
from database import Base, get_db
from models import Equipo, Jugador, Partido
from passlib.context import CryptContext

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_vidartcamp.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(scope="function")
def setup_database():
    """Setup test database with sample data"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    # Create teams
    equipo1 = Equipo(nombre="Equipo Test 1", activo=True)
    equipo2 = Equipo(nombre="Equipo Test 2", activo=True)
    db.add_all([equipo1, equipo2])
    db.commit()
    db.refresh(equipo1)
    db.refresh(equipo2)
    
    # Create players
    jugador1 = Jugador(
        dni="111",
        nombre_completo="Test Player 1",
        password_hash=pwd_context.hash("test123"),
        equipo_id=equipo1.id
    )
    jugador2 = Jugador(
        dni="222",
        nombre_completo="Test Player 2",
        password_hash=pwd_context.hash("test123"),
        equipo_id=equipo2.id
    )
    db.add_all([jugador1, jugador2])
    db.commit()
    
    # Create match for today
    partido = Partido(
        equipo_local_id=equipo1.id,
        equipo_visitante_id=equipo2.id,
        fecha=date.today(),
        hora=dt_time(18, 0)
    )
    db.add(partido)
    db.commit()
    
    db.close()
    
    yield
    
    # Cleanup
    Base.metadata.drop_all(bind=engine)

def test_login_page_loads():
    """Test that login page loads correctly"""
    response = client.get("/login")
    assert response.status_code == 200
    assert b"Bienvenido" in response.content

def test_login_with_valid_credentials(setup_database):
    """Test login with valid credentials"""
    response = client.post(
        "/login",
        data={"dni": "111", "password": "test123"},
        follow_redirects=False
    )
    assert response.status_code == 302
    assert response.headers["location"] == "/"
    assert "access_token" in response.cookies

def test_login_with_invalid_credentials(setup_database):
    """Test login with invalid credentials"""
    response = client.post(
        "/login",
        data={"dni": "111", "password": "wrongpassword"}
    )
    assert response.status_code == 200
    assert b"incorrectos" in response.content

def test_dashboard_requires_auth():
    """Test that dashboard requires authentication"""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/login"

def test_dashboard_with_auth(setup_database):
    """Test dashboard access with authentication"""
    # Login first
    login_response = client.post(
        "/login",
        data={"dni": "111", "password": "test123"},
        follow_redirects=False
    )
    cookies = login_response.cookies
    
    # Access dashboard
    response = client.get("/", cookies=cookies)
    assert response.status_code == 200
    assert b"Test Player 1" in response.content
    assert b"Tienes partido hoy" in response.content

def test_generate_qr_without_auth():
    """Test QR generation without authentication"""
    response = client.post("/api/generar-qr")
    assert response.status_code == 401

def test_generate_qr_with_auth(setup_database):
    """Test QR generation with authentication"""
    # Login first
    login_response = client.post(
        "/login",
        data={"dni": "111", "password": "test123"}
    )
    cookies = login_response.cookies
    
    # Generate QR
    response = client.post("/api/generar-qr", cookies=cookies)
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert "expiracion_segundos" in data
    assert data["expiracion_segundos"] == 120

def test_scanner_page_loads():
    """Test that scanner page loads"""
    response = client.get("/scanner")
    assert response.status_code == 200
    assert b"Esc" in response.content

def test_validate_qr_with_invalid_token():
    """Test QR validation with invalid token"""
    response = client.post(
        "/api/validar-qr",
        json={"token": "invalid-token-123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"

def test_validate_qr_flow(setup_database):
    """Test complete QR validation flow"""
    # Login
    login_response = client.post(
        "/login",
        data={"dni": "111", "password": "test123"}
    )
    cookies = login_response.cookies
    
    # Generate QR
    qr_response = client.post("/api/generar-qr", cookies=cookies)
    token = qr_response.json()["token"]
    
    # Validate QR
    validate_response = client.post(
        "/api/validar-qr",
        json={"token": token}
    )
    assert validate_response.status_code == 200
    data = validate_response.json()
    assert data["status"] == "ok"
    assert data["nombre"] == "Test Player 1"
    assert data["equipo"] == "Equipo Test 1"
    
    # Try to use same QR again (should fail)
    validate_response2 = client.post(
        "/api/validar-qr",
        json={"token": token}
    )
    data2 = validate_response2.json()
    assert data2["status"] == "error"
    assert "ya utilizado" in data2["mensaje"]

def test_logout():
    """Test logout functionality"""
    response = client.get("/logout", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/login"
    assert response.cookies.get("access_token", "") == ""

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
