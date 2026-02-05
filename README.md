# 🏟️ Vidartcamp - Sistema de Control de Acceso

Sistema de control de acceso mediante códigos QR para complejo deportivo. Permite a los jugadores con partidos programados generar pases temporales de entrada.

## 🎯 Características

- ✅ Login con DNI y contraseña
- ✅ Generación de QR temporal (validez 120 segundos)
- ✅ Validación automática de partidos del día
- ✅ Escáner QR con cámara del celular
- ✅ Interfaz responsive (móvil y desktop)
- ✅ Control de acceso basado en calendario de partidos

## 🛠️ Stack Tecnológico

- **Backend:** Python 3.10+ con FastAPI
- **Base de Datos:** SQLite con SQLAlchemy ORM
- **Frontend:** Jinja2 Templates + TailwindCSS
- **Servidor:** Uvicorn
- **Seguridad:** Bcrypt (contraseñas) + JWT (sesiones)
- **QR:** QRCode.js (generación) + html5-qrcode (lectura)

## 📁 Estructura del Proyecto

```
vidartcamp/
├── main.py              # Aplicación principal y rutas
├── database.py          # Configuración de SQLite
├── models.py            # Modelos de base de datos
├── requirements.txt     # Dependencias Python
├── templates/           # Templates HTML
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   └── scanner.html
├── vidartcamp.db        # Base de datos (generada automáticamente)
├── README.md            # Este archivo
└── DEPLOY.md            # Guía de despliegue
```

## 🚀 Instalación Local

### 1. Clonar el repositorio
```bash
git clone https://github.com/tu-usuario/vidartcamp.git
cd vidartcamp
```

### 2. Crear entorno virtual
```bash
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Ejecutar la aplicación
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Acceder a la aplicación
Abre tu navegador en: `http://localhost:8000`

## 👤 Usuarios de Prueba

La aplicación se inicializa con datos de prueba:

| DNI | Contraseña | Nombre | Equipo |
|-----|------------|--------|---------|
| 123 | 1234 | Juan Pérez | Los Rayos |
| 456 | 1234 | Carlos González | Los Truenos |

**Nota:** Hay un partido programado para HOY entre ambos equipos, por lo que ambos jugadores pueden generar QR.

## 📱 Flujo de Uso

### Para Jugadores:
1. Ingresar a `vidartcamp.com`
2. Login con DNI y contraseña
3. Si tiene partido hoy → Botón "Generar Pase de Entrada"
4. Se genera QR con validez de 2 minutos
5. Mostrar QR al portero

### Para Porteros:
1. Ingresar a `vidartcamp.com/scanner`
2. Permitir acceso a la cámara
3. Escanear QR del jugador
4. Ver resultado:
   - ✅ **Verde:** Acceso permitido (muestra nombre y equipo)
   - ❌ **Rojo:** Acceso denegado (muestra motivo)

## 🔒 Seguridad

- Contraseñas hasheadas con bcrypt
- Tokens JWT para sesiones
- QR de un solo uso
- Expiración automática de QR (120 segundos)
- HTTPS obligatorio para producción (cámara requiere SSL)

## 🗃️ Modelo de Base de Datos

### Equipos
- `id`: Identificador único
- `nombre`: Nombre del equipo
- `activo`: Estado del equipo

### Jugadores
- `id`: Identificador único
- `dni`: DNI (usado como username)
- `nombre_completo`: Nombre del jugador
- `password_hash`: Contraseña hasheada
- `equipo_id`: Relación con equipo

### Partidos
- `id`: Identificador único
- `equipo_local_id`: Equipo local
- `equipo_visitante_id`: Equipo visitante
- `fecha`: Fecha del partido
- `hora`: Hora del partido

### SesionesQR
- `token`: UUID del QR
- `jugador_id`: Jugador que generó el QR
- `fecha_expiracion`: Timestamp de expiración
- `usado`: Bandera de uso único

## 🌐 Despliegue a Producción

Para desplegar en vidartcamp.com, consulta la guía completa en [DEPLOY.md](DEPLOY.md)

**Opciones de hosting:**
- VPS (DigitalOcean, Linode, AWS EC2)
- Railway (Recomendado - HTTPS automático)
- Render (Alternativa con HTTPS automático)

**⚠️ IMPORTANTE:** HTTPS es obligatorio para que la cámara funcione en el escáner.

## 🔧 Configuración

### Cambiar SECRET_KEY (OBLIGATORIO en producción)
En `main.py`, línea ~30:
```python
SECRET_KEY = "tu-clave-secreta-generada-con-openssl-rand-hex-32"
```

### Ajustar tiempo de expiración del QR
En `main.py`, línea ~28:
```python
QR_EXPIRATION_SECONDS = 120  # Cambiar según necesidad
```

## 🧪 Testing

Para probar localmente con HTTPS (necesario para la cámara):

### Opción 1: Usar ngrok
```bash
ngrok http 8000
```

### Opción 2: Certificado autofirmado
```bash
uvicorn main:app --host 0.0.0.0 --port 8443 --ssl-keyfile=key.pem --ssl-certfile=cert.pem
```

## 📊 Agregar Más Datos

Para agregar más equipos, jugadores y partidos, puedes:

1. **Vía código:** Modificar el evento `startup_event` en `main.py`
2. **Vía SQL directo:** Conectar a `vidartcamp.db` con un cliente SQLite
3. **Crear panel de admin:** Agregar rutas CRUD para gestión

## 🐛 Solución de Problemas

### La cámara no funciona
- Asegúrate de estar usando HTTPS
- Verifica permisos de cámara en el navegador
- Chrome: `chrome://settings/content/camera`

### Error al generar QR
- Verifica que el jugador tenga partido HOY
- Revisa los logs del servidor
- Confirma que la base de datos tenga partidos

### No puedo hacer login
- Verifica usuarios de prueba: DNI "123" o "456", password "1234"
- Revisa que la base de datos se haya inicializado
- Mira los logs: `journalctl -u vidartcamp -f` (en VPS)

## 📈 Mejoras Futuras

- [ ] Panel de administración para gestionar equipos/jugadores/partidos
- [ ] Notificaciones push cuando se genera QR
- [ ] Estadísticas de accesos
- [ ] Integración con calendario externo
- [ ] App móvil nativa
- [ ] Historial de accesos por jugador
- [ ] Reportes de asistencia por equipo

## 📄 Licencia

Este proyecto es de código abierto y está disponible bajo la licencia MIT.

## 👥 Contribuir

Las contribuciones son bienvenidas. Por favor:
1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📞 Soporte

Para preguntas o problemas:
- Abre un issue en GitHub
- Revisa [DEPLOY.md](DEPLOY.md) para problemas de despliegue

---

Desarrollado con ❤️ para Vidartcamp
