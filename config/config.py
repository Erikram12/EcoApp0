"""
Configuración del Sistema de Reciclaje Inteligente
==================================================

Este módulo contiene todas las configuraciones, constantes y variables de entorno
utilizadas en el sistema de reciclaje.
"""

import os
import warnings

# =========================
# Configuración MQTT
# =========================
MQTT_BROKER = os.getenv("MQTT_BROKER", "2e139bb9a6c5438b89c85c91b8cbd53f.s1.eu.hivemq.cloud")
MQTT_PORT = int(os.getenv("MQTT_PORT", "8883"))
MQTT_USER = os.getenv("MQTT_USER", "ramsi")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "Erikram2025")
MQTT_MATERIAL_TOPIC = os.getenv("MQTT_MATERIAL_TOPIC", "material/detectado")  # Tópico para materiales detectados

MQTT_TOPIC = os.getenv("MQTT_TOPIC", "reciclaje/+/nivel")  # + = cualquier deviceId

# =========================
# Configuración MQTT para ESP32
# =========================
MQTT_ESP32_TOPIC = os.getenv("MQTT_ESP32_TOPIC", "reciclaje/esp32/command")  # Tópico para comandos a ESP32

# =========================
# Configuración Firebase
# =========================
FIREBASE_DB_URL = os.getenv("FIREBASE_DB_URL", "https://resiclaje-39011-default-rtdb.firebaseio.com/")
FIREBASE_CRED_PATH = os.getenv("FIREBASE_CRED_PATH", "config/resiclaje-39011-firebase-adminsdk-fbsvc-433ec62b6c.json")

# =========================
# Constantes del Sistema
# =========================
ALLOWED_STATES = {"Vacío", "Medio", "Lleno"}
ALLOWED_TARGETS = {"contePlastico", "conteAluminio"}

# =========================
# Configuración de Puntos
# =========================
POINTS_PLASTIC = 20
POINTS_ALUMINUM = 30

# =========================
# Configuración de Sesión
# =========================
SESSION_DURATION = 20  # segundos

# =========================
# Configuración de Timeout de Puntos
# =========================
POINTS_CLAIM_TIMEOUT = 10  # segundos para reclamar puntos antes del reinicio

# =========================
# Configuración YOLO
# =========================
CONFIDENCE_THRESHOLD = 0.95  # Confianza mínima para detección (95%)
YOLO_MODEL_PATH = "best.onnx"  # Ruta del modelo YOLO
YOLO_IMAGE_SIZE = 320  # Tamaño de imagen para YOLO
YOLO_CONFIDENCE = 0.6  # Confianza mínima para YOLO

# =========================
# Configuración de UI
# =========================
WINDOW_TITLE = "Sistema de Reciclaje Inteligente - Panel de Visualización"
WINDOW_SIZE = "1200x700"  # Resolución para computadora
WINDOW_BG_COLOR = '#2c3e50'
FRAME_BG_COLOR = '#34495e'
TEXT_COLOR = '#ecf0f1'

# =========================
# Configuración para Pantalla Pequeña
# =========================
COMPACT_MODE = True  # Modo compacto para pantalla LCD
FONT_SIZE_SMALL = 8
FONT_SIZE_MEDIUM = 10
FONT_SIZE_LARGE = 12

# Colores para estados
STATUS_COLORS = {
    "success": "#27ae60",
    "error": "#e74c3c",
    "warning": "#f39c12",
    "info": "#3498db"
}

# Colores para contenedores
CONTAINER_COLORS = {
    "Lleno": "#e74c3c",    # Rojo
    "Medio": "#f39c12",    # Naranja
    "Vacío": "#27ae60"     # Verde
}

# Emojis para contenedores
CONTAINER_EMOJIS = {
    "Lleno": "🔴",
    "Medio": "🟡",
    "Vacío": "🟢"
}

# =========================
# Configuración de Logging
# =========================
warnings.filterwarnings("ignore", category=DeprecationWarning)
