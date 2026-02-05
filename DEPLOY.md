# CÓMO SUBIR ESTO A PRODUCCIÓN EN VIDARTCAMP.COM

## 📋 TABLA DE CONTENIDOS
1. Preparación del código
2. Opción A: Despliegue en VPS (Servidor Propio)
3. Opción B: Despliegue en Railway (Recomendado para principiantes)
4. Opción C: Despliegue en Render
5. Configuración de HTTPS/SSL (CRÍTICO)
6. Configuración del dominio vidartcamp.com
7. Verificación final

---

## 1. PREPARACIÓN DEL CÓDIGO

Antes de desplegar, asegúrate de tener todos los archivos:

```
vidartcamp/
├── main.py
├── database.py
├── models.py
├── requirements.txt
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   └── scanner.html
└── vidartcamp.db (se creará automáticamente)
```

**IMPORTANTE:** Cambia el SECRET_KEY en main.py antes de desplegar:
```python
# En main.py, línea ~30
SECRET_KEY = "TU-CLAVE-SUPER-SECRETA-AQUI-GENERAR-CON-openssl-rand-hex-32"
```

Genera una clave segura ejecutando:
```bash
openssl rand -hex 32
```

---

## 2. OPCIÓN A: DESPLIEGUE EN VPS (SERVIDOR PROPIO)

### Paso 1: Conectar al servidor
```bash
ssh root@TU_IP_DEL_SERVIDOR
```

### Paso 2: Instalar dependencias del sistema
```bash
apt update
apt install python3-pip python3-venv nginx certbot python3-certbot-nginx -y
```

### Paso 3: Crear usuario y directorio
```bash
useradd -m -s /bin/bash vidartcamp
su - vidartcamp
```

### Paso 4: Subir el código
Opción A - Usando Git:
```bash
git clone https://tu-repositorio.git vidartcamp-app
cd vidartcamp-app
```

Opción B - Usando SCP desde tu computadora local:
```bash
# Ejecutar desde tu computadora
scp -r ./vidartcamp-app vidartcamp@TU_IP:/home/vidartcamp/
```

### Paso 5: Crear entorno virtual e instalar dependencias
```bash
cd ~/vidartcamp-app
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Paso 6: Crear servicio systemd
Como root, crear el archivo `/etc/systemd/system/vidartcamp.service`:

```ini
[Unit]
Description=Vidartcamp Control de Acceso
After=network.target

[Service]
User=vidartcamp
WorkingDirectory=/home/vidartcamp/vidartcamp-app
Environment="PATH=/home/vidartcamp/vidartcamp-app/venv/bin"
ExecStart=/home/vidartcamp/vidartcamp-app/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000

[Install]
WantedBy=multi-user.target
```

### Paso 7: Activar y iniciar el servicio
```bash
systemctl daemon-reload
systemctl enable vidartcamp
systemctl start vidartcamp
systemctl status vidartcamp
```

### Paso 8: Configurar Nginx como proxy inverso
Crear `/etc/nginx/sites-available/vidartcamp`:

```nginx
server {
    listen 80;
    server_name vidartcamp.com www.vidartcamp.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Activar el sitio:
```bash
ln -s /etc/nginx/sites-available/vidartcamp /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx
```

### Paso 9: Configurar SSL con Let's Encrypt (¡CRÍTICO!)
```bash
certbot --nginx -d vidartcamp.com -d www.vidartcamp.com
```

Sigue las instrucciones. Certbot configurará automáticamente HTTPS.

---

## 3. OPCIÓN B: DESPLIEGUE EN RAILWAY (RECOMENDADO)

### Paso 1: Crear cuenta en Railway
- Ve a https://railway.app
- Regístrate con GitHub

### Paso 2: Subir código a GitHub
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/tu-usuario/vidartcamp.git
git push -u origin main
```

### Paso 3: Crear proyecto en Railway
1. Click en "New Project"
2. Selecciona "Deploy from GitHub repo"
3. Autoriza Railway a acceder a tu repositorio
4. Selecciona tu repositorio

### Paso 4: Configurar variables de entorno
En Railway, ve a Variables y agrega:
```
PORT=8000
SECRET_KEY=tu-clave-secreta-aqui
```

### Paso 5: Configurar el comando de inicio
Railway debería detectar automáticamente que es una app Python. Si no, agrega un `Procfile`:

```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

### Paso 6: Configurar dominio personalizado
1. En Railway, ve a Settings > Domains
2. Click en "Generate Domain" (te dará un dominio temporal)
3. Click en "Custom Domain" y agrega `vidartcamp.com`
4. Railway te dará un CNAME para configurar en tu DNS

**Railway proporciona HTTPS automáticamente** ✅

---

## 4. OPCIÓN C: DESPLIEGUE EN RENDER

### Paso 1: Crear cuenta en Render
- Ve a https://render.com
- Regístrate con GitHub

### Paso 2: Crear Web Service
1. Click en "New +"
2. Selecciona "Web Service"
3. Conecta tu repositorio de GitHub

### Paso 3: Configurar el servicio
- **Name:** vidartcamp
- **Region:** Oregon (o el más cercano)
- **Branch:** main
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`

### Paso 4: Variables de entorno
Agrega en "Environment":
```
SECRET_KEY=tu-clave-secreta-aqui
```

### Paso 5: Configurar dominio
1. En el dashboard de tu servicio, ve a "Settings"
2. Scroll hasta "Custom Domain"
3. Agrega `vidartcamp.com`
4. Render te proporcionará instrucciones para configurar DNS

**Render proporciona HTTPS automáticamente** ✅

---

## 5. CONFIGURACIÓN DE HTTPS/SSL (CRÍTICO)

### ⚠️ POR QUÉ ES CRÍTICO HTTPS

**La cámara del celular NO funciona en HTTP por razones de seguridad del navegador.**

Los navegadores modernos requieren HTTPS para:
- Acceder a la cámara
- Acceder al micrófono
- Geolocalización
- Otras APIs sensibles

### Verificar que HTTPS está funcionando

1. Visita tu sitio: `https://vidartcamp.com`
2. Verifica que hay un candado 🔒 en la barra de direcciones
3. Click en el candado y verifica que el certificado es válido

### Solución de problemas

Si HTTPS no funciona:

**En VPS:**
```bash
# Verificar certificado
certbot certificates

# Renovar certificado
certbot renew

# Verificar Nginx
nginx -t
systemctl status nginx
```

**En Railway/Render:**
- HTTPS es automático, pero asegúrate de que tu dominio apunta correctamente
- Espera 24-48 horas para propagación DNS

---

## 6. CONFIGURACIÓN DEL DOMINIO VIDARTCAMP.COM

### En tu proveedor de DNS (GoDaddy, Namecheap, etc.)

**Para VPS (IP directa):**
```
Tipo: A
Nombre: @
Valor: TU_IP_DEL_SERVIDOR
TTL: 3600

Tipo: A
Nombre: www
Valor: TU_IP_DEL_SERVIDOR
TTL: 3600
```

**Para Railway:**
```
Tipo: CNAME
Nombre: @
Valor: el-valor-que-railway-te-proporciono.up.railway.app
TTL: 3600
```

**Para Render:**
```
Tipo: CNAME
Nombre: @
Valor: el-valor-que-render-te-proporciono.onrender.com
TTL: 3600
```

### Verificar propagación DNS
```bash
dig vidartcamp.com
# o
nslookup vidartcamp.com
```

---

## 7. VERIFICACIÓN FINAL

### Checklist de pruebas:

- [ ] ✅ El sitio carga en `https://vidartcamp.com`
- [ ] ✅ Hay un candado 🔒 en la barra de direcciones
- [ ] ✅ Puedes hacer login con DNI "123" y password "1234"
- [ ] ✅ Aparece mensaje "Tienes partido hoy"
- [ ] ✅ Puedes generar un QR
- [ ] ✅ El QR se muestra correctamente
- [ ] ✅ El contador de 120 segundos funciona
- [ ] ✅ La página `/scanner` carga
- [ ] ✅ El navegador pide permiso para usar la cámara
- [ ] ✅ La cámara se activa correctamente
- [ ] ✅ Al escanear el QR, muestra "ACCESO PERMITIDO" en verde
- [ ] ✅ Al escanear el mismo QR otra vez, muestra "QR ya utilizado"

### Probar en diferentes dispositivos:

1. **Desktop:** Chrome, Firefox
2. **Móvil:** Chrome en Android, Safari en iPhone
3. **Tablet:** iPad, Android Tablet

---

## 🚀 COMANDOS RÁPIDOS DE REFERENCIA

### Iniciar aplicación localmente (desarrollo)
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Iniciar aplicación en producción (VPS)
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Ver logs (systemd en VPS)
```bash
journalctl -u vidartcamp -f
```

### Reiniciar servicio (VPS)
```bash
systemctl restart vidartcamp
```

### Verificar certificado SSL
```bash
openssl s_client -connect vidartcamp.com:443 -servername vidartcamp.com
```

---

## 📞 SOPORTE Y SOLUCIÓN DE PROBLEMAS

### Problema: "La cámara no funciona"
- Verifica que estés usando HTTPS (no HTTP)
- En Chrome, ve a chrome://settings/content/camera y permite vidartcamp.com
- Asegúrate de que el certificado SSL sea válido

### Problema: "QR no válido"
- Verifica que la base de datos esté inicializada
- Revisa que haya partidos para HOY en la base de datos
- Mira los logs del servidor

### Problema: "Error 502 Bad Gateway"
- El servicio uvicorn no está corriendo
- Verifica: `systemctl status vidartcamp`
- Revisa logs: `journalctl -u vidartcamp -n 50`

### Problema: "No puedo hacer login"
- Verifica que la base de datos exista y tenga datos
- Los usuarios de prueba son DNI "123" y "456" con password "1234"

---

## 🔐 SEGURIDAD ADICIONAL (RECOMENDADO)

1. **Cambiar SECRET_KEY:** Ya lo hicimos arriba
2. **Firewall en VPS:**
```bash
ufw allow 22
ufw allow 80
ufw allow 443
ufw enable
```

3. **Agregar autenticación al scanner:**
En `main.py`, modifica la ruta `/scanner` para requerir login de admin.

4. **Backups automáticos de la BD:**
```bash
# Crontab para backup diario
0 2 * * * cp /home/vidartcamp/vidartcamp-app/vidartcamp.db /home/vidartcamp/backups/vidartcamp-$(date +\%Y\%m\%d).db
```

---

## ✅ ¡LISTO!

Tu sistema de control de acceso está ahora en producción en **vidartcamp.com** con HTTPS funcionando.

Los jugadores pueden:
1. Entrar a vidartcamp.com
2. Loguearse con su DNI
3. Generar su QR si tienen partido hoy
4. Mostrarlo al portero

El portero puede:
1. Entrar a vidartcamp.com/scanner
2. Escanear el QR del jugador
3. Ver si el acceso es válido o no

**¡El escáner funcionará perfectamente porque HTTPS está configurado!** 🎉
