#!/bin/bash
# Script de inicio para desarrollo local

echo "🚀 Iniciando Vidartcamp..."
echo ""

# Verificar que estamos en el directorio correcto
if [ ! -f "main.py" ]; then
    echo "❌ Error: No se encuentra main.py"
    echo "   Asegúrate de ejecutar este script desde el directorio del proyecto"
    exit 1
fi

# Verificar que el entorno virtual existe
if [ ! -d "venv" ]; then
    echo "📦 Creando entorno virtual..."
    python3 -m venv venv
fi

# Activar entorno virtual
echo "🔧 Activando entorno virtual..."
source venv/bin/activate

# Instalar/actualizar dependencias
echo "📥 Instalando dependencias..."
pip install -q -r requirements.txt

# Verificar si existe la base de datos
if [ ! -f "vidartcamp.db" ]; then
    echo "📊 La base de datos se creará automáticamente con datos de prueba"
fi

echo ""
echo "✅ Todo listo!"
echo ""
echo "🌐 Abriendo servidor en http://localhost:8000"
echo "📱 Para probar el escáner: http://localhost:8000/scanner"
echo ""
echo "👤 Usuarios de prueba:"
echo "   DNI: 123 | Password: 1234"
echo "   DNI: 456 | Password: 1234"
echo ""
echo "⚠️  Nota: La cámara solo funciona con HTTPS en producción"
echo "   Para probar localmente con cámara, usa ngrok o similar"
echo ""
echo "Presiona Ctrl+C para detener el servidor"
echo ""

# Iniciar servidor
uvicorn main:app --reload --host 0.0.0.0 --port 8000
