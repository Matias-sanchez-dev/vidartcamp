# 🚀 GUÍA DE INICIO RÁPIDO

## Instalación en 3 pasos

### 1️⃣ Clonar e instalar
```bash
git clone https://github.com/tu-usuario/vidartcamp.git
cd vidartcamp
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2️⃣ Iniciar servidor
```bash
# Opción A: Script automático (Linux/Mac)
./start.sh

# Opción B: Comando manual
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3️⃣ Probar la aplicación
- **Login:** http://localhost:8000
- **Escáner:** http://localhost:8000/scanner

**Usuarios de prueba:**
- DNI: `123` o `456` | Password: `1234`

---

## 📱 Flujo de Uso

### Para Jugadores:
1. Abrir navegador → `vidartcamp.com`
2. Login con DNI y contraseña
3. Si tiene partido hoy → Click "Generar Pase de Entrada"
4. Mostrar QR al portero (válido 2 minutos)

### Para Porteros:
1. Abrir navegador → `vidartcamp.com/scanner`
2. Permitir acceso a cámara
3. Escanear QR del jugador
4. Ver resultado: ✅ Verde (OK) o ❌ Rojo (Denegado)

---

## 🛠️ Gestión de Datos

### Agregar equipos/jugadores/partidos:
```bash
python db_utils.py add-team      # Agregar equipo
python db_utils.py add-player    # Agregar jugador
python db_utils.py add-match     # Agregar partido
```

### Listar datos:
```bash
python db_utils.py list-teams    # Ver equipos
python db_utils.py list-players  # Ver jugadores
python db_utils.py list-matches  # Ver partidos
python db_utils.py list-qr       # Ver sesiones QR
```

### Resetear base de datos:
```bash
python db_utils.py reset         # Borrar todo
python db_utils.py init          # Recrear con datos de prueba
```

---

## 🌐 Despliegue a Producción

### Opción más fácil: Railway
```bash
# 1. Subir a GitHub
git init
git add .
git commit -m "Initial commit"
git push

# 2. Ir a railway.app
# 3. New Project → Deploy from GitHub
# 4. Seleccionar repo
# 5. Listo! Railway da HTTPS automático
```

**Ver guía completa:** [DEPLOY.md](DEPLOY.md)

---

## 🧪 Testing

```bash
# Ejecutar tests
pytest test_main.py -v

# Test específico
pytest test_main.py::test_login_with_valid_credentials -v

# Con coverage
pytest --cov=main test_main.py
```

---

## 🐛 Troubleshooting

### ❌ "La cámara no funciona"
- ✅ **Solución:** Usar HTTPS (obligatorio)
- En desarrollo: usar ngrok o similar
- En producción: Railway/Render dan HTTPS gratis

### ❌ "No puedo hacer login"
- ✅ **Solución:** Usar DNI `123` o `456` con password `1234`
- O crear tu propio usuario con `python db_utils.py add-player`

### ❌ "Error al generar QR"
- ✅ **Solución:** El jugador debe tener partido HOY
- Crear partido: `python db_utils.py add-match`

### ❌ "ModuleNotFoundError"
- ✅ **Solución:** Instalar dependencias
```bash
pip install -r requirements.txt
```

---

## 📚 Archivos Importantes

| Archivo | Descripción |
|---------|-------------|
| `main.py` | Aplicación principal |
| `models.py` | Modelos de base de datos |
| `templates/` | Plantillas HTML |
| `db_utils.py` | Utilidades de BD |
| `DEPLOY.md` | Guía de despliegue completa |
| `README.md` | Documentación completa |

---

## 🔒 Seguridad

**Antes de producción:**
1. Cambiar `SECRET_KEY` en `main.py`
2. Usar variables de entorno (`.env`)
3. Habilitar HTTPS
4. Agregar autenticación al scanner

---

## 💡 Tips

- **Backup:** `cp vidartcamp.db vidartcamp-backup.db`
- **Ver logs:** `journalctl -u vidartcamp -f` (en VPS)
- **Puerto ocupado:** Cambiar `--port 8000` a otro número
- **Probar HTTPS local:** Usar ngrok `ngrok http 8000`

---

## 📞 Ayuda

- **Bugs:** Abrir issue en GitHub
- **Docs completas:** Ver [README.md](README.md)
- **Deploy:** Ver [DEPLOY.md](DEPLOY.md)

---

**¡Todo listo! 🎉**

Ahora tienes un sistema de control de acceso completamente funcional.

```
📱 Jugadores → Login → Generar QR → Mostrar al portero
👮 Portero → Scanner → Validar → Permitir/Denegar acceso
```
