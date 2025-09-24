import os
import ssl
import time
import cv2
import numpy as np
from pathlib import Path
from ultralytics import YOLO
import paho.mqtt.client as mqtt
from smartcard.System import readers
from smartcard.Exceptions import NoCardException, CardConnectionException
import firebase_admin
from firebase_admin import credentials, db
import threading
import math

# ---------- CONFIG MQTT ----------
MQTT_BROKER = os.getenv("MQTT_BROKER", "2e139bb9a6c5438b89c85c91b8cbd53f.s1.eu.hivemq.cloud")
MQTT_PORT = int(os.getenv("MQTT_PORT", "8883"))
MQTT_USER = os.getenv("MQTT_USER", "ramsi")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "Erikram2025")
MQTT_MATERIAL_TOPIC = os.getenv("MQTT_MATERIAL_TOPIC", "material/detectado")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
client.tls_set(cert_reqs=ssl.CERT_NONE)
client.tls_insecure_set(True)
client.connect(MQTT_BROKER, MQTT_PORT)
client.loop_start()

# ---------- CONFIG FIREBASE ----------
SERVICE_ACCOUNT_PATH = "config/resiclaje-39011-firebase-adminsdk-fbsvc-433ec62b6c.json"
DATABASE_URL = "https://resiclaje-39011-default-rtdb.firebaseio.com"

cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
firebase_admin.initialize_app(cred, {'databaseURL': DATABASE_URL})

nfc_index_ref = db.reference('nfc_index')
usuarios_ref = db.reference('usuarios')
GET_UID_APDU = [0xFF, 0xCA, 0x00, 0x00, 0x00]

# ---------- ESTADO GLOBAL ----------
material_detectado = None  # "plastico" o "aluminio"
lock = threading.Lock()

# ---------- VARIABLES PARA ANIMACIONES ----------
animation_time = 0
pulse_alpha = 0
wave_radius = 0
particle_system = []

# ---------- COLORES Y ESTILOS ----------
COLORS = {
    'primary': (0, 188, 212),  # Cyan
    'secondary': (76, 175, 80),  # Green
    'accent': (255, 193, 7),  # Amber
    'success': (76, 175, 80),  # Green
    'warning': (255, 152, 0),  # Orange
    'error': (244, 67, 54),  # Red
    'white': (255, 255, 255),
    'dark': (33, 33, 33),
    'plastico': (33, 150, 243),  # Blue
    'aluminio': (158, 158, 158)  # Grey
}


class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.vx = np.random.uniform(-2, 2)
        self.vy = np.random.uniform(-2, 2)
        self.life = 1.0
        self.color = color
        self.size = np.random.uniform(2, 6)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 0.02
        self.vy += 0.1  # gravedad
        return self.life > 0

    def draw(self, frame):
        if self.life > 0:
            alpha = max(0, self.life)
            color = tuple(int(c * alpha) for c in self.color)
            cv2.circle(frame, (int(self.x), int(self.y)), int(self.size * alpha), color, -1)


def create_gradient_background(height, width, color1, color2):
    """Crea un fondo con gradiente"""
    background = np.zeros((height, width, 3), dtype=np.uint8)
    for i in range(height):
        ratio = i / height
        for j in range(3):
            background[i, :, j] = int(color1[j] * (1 - ratio) + color2[j] * ratio)
    return background


def draw_animated_border(frame, thickness=3, color=(0, 188, 212)):
    """Dibuja un borde animado"""
    h, w = frame.shape[:2]
    time_factor = time.time() * 2

    # Líneas animadas en las esquinas
    corner_length = 50
    alpha = (math.sin(time_factor) + 1) / 2
    border_color = tuple(int(c * (0.5 + alpha * 0.5)) for c in color)

    # Esquina superior izquierda
    cv2.line(frame, (0, 0), (corner_length, 0), border_color, thickness)
    cv2.line(frame, (0, 0), (0, corner_length), border_color, thickness)

    # Esquina superior derecha
    cv2.line(frame, (w - corner_length, 0), (w, 0), border_color, thickness)
    cv2.line(frame, (w, 0), (w, corner_length), border_color, thickness)

    # Esquina inferior izquierda
    cv2.line(frame, (0, h - corner_length), (0, h), border_color, thickness)
    cv2.line(frame, (0, h), (corner_length, h), border_color, thickness)

    # Esquina inferior derecha
    cv2.line(frame, (w - corner_length, h), (w, h), border_color, thickness)
    cv2.line(frame, (w, h - corner_length), (w, h), border_color, thickness)


def draw_loading_spinner(frame, x, y, radius=30, color=(255, 255, 255)):
    """Dibuja un spinner de carga animado"""
    time_factor = time.time() * 3
    for i in range(8):
        angle = (i * 45 + time_factor * 50) * math.pi / 180
        start_x = int(x + (radius - 10) * math.cos(angle))
        start_y = int(y + (radius - 10) * math.sin(angle))
        end_x = int(x + radius * math.cos(angle))
        end_y = int(y + radius * math.sin(angle))

        alpha = (i + 1) / 8
        line_color = tuple(int(c * alpha) for c in color)
        cv2.line(frame, (start_x, start_y), (end_x, end_y), line_color, 3)


def draw_progress_bar(frame, progress, x, y, width=300, height=20, color=(0, 188, 212)):
    """Dibuja una barra de progreso animada"""
    # Fondo de la barra
    cv2.rectangle(frame, (x, y), (x + width, y + height), COLORS['dark'], -1)
    cv2.rectangle(frame, (x, y), (x + width, y + height), COLORS['white'], 2)

    # Progreso
    fill_width = int(width * progress)
    if fill_width > 0:
        # Efecto de brillo
        for i in range(fill_width):
            brightness = 1.0 - abs(i - fill_width / 2) / (fill_width / 2 + 1)
            bar_color = tuple(int(c * (0.7 + brightness * 0.3)) for c in color)
            cv2.line(frame, (x + i, y), (x + i, y + height), bar_color, 1)


def draw_pulsing_circle(frame, x, y, base_radius=50, color=(0, 255, 0)):
    """Dibuja un círculo pulsante"""
    time_factor = time.time() * 2
    pulse = (math.sin(time_factor) + 1) / 2
    radius = int(base_radius * (0.8 + pulse * 0.4))
    alpha = 0.3 + pulse * 0.4

    circle_color = tuple(int(c * alpha) for c in color)
    cv2.circle(frame, (x, y), radius, circle_color, 3)
    cv2.circle(frame, (x, y), radius - 10, circle_color, 1)


def draw_floating_text(frame, text, x, y, font_scale=1, color=(255, 255, 255), shadow=True):
    """Dibuja texto con efecto flotante"""
    time_factor = time.time() * 2
    offset_y = int(5 * math.sin(time_factor))

    if shadow:
        # Sombra
        cv2.putText(frame, text, (x + 2, y + offset_y + 2),
                    cv2.FONT_HERSHEY_SIMPLEX, font_scale, COLORS['dark'], 2, cv2.LINE_AA)

    # Texto principal
    cv2.putText(frame, text, (x, y + offset_y),
                cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, 2, cv2.LINE_AA)


def create_particles(x, y, color, count=20):
    """Crea partículas para efectos"""
    global particle_system
    for _ in range(count):
        particle_system.append(Particle(x, y, color))


def update_particles(frame):
    """Actualiza y dibuja todas las partículas"""
    global particle_system
    particle_system = [p for p in particle_system if p.update()]
    for particle in particle_system:
        particle.draw(frame)


# ---------- NFC ----------
def get_reader():
    r = readers()
    if not r:
        raise RuntimeError("No se detectaron lectores PC/SC.")
    return r[0]


def bytes_to_hex_str(data_bytes):
    return ''.join('{:02X}'.format(b) for b in data_bytes)


def buscar_usuario_por_uid(uid_hex):
    mapping = nfc_index_ref.get() or {}
    user_id = mapping.get(uid_hex.upper())
    if not user_id:
        return None, None
    user = usuarios_ref.child(user_id).get()
    return user_id, user


def loop_nfc():
    global material_detectado, particle_system
    lector = get_reader()
    conn = lector.createConnection()
    last_uid = None
    print("[NFC] Esperando tarjetas...")

    while True:
        try:
            conn.connect()
            data, sw1, sw2 = conn.transmit(GET_UID_APDU)
            if sw1 == 0x90 and sw2 == 0x00 and data:
                uid = bytes_to_hex_str(data)
                if uid != last_uid:
                    print(f"[NFC] UID detectado: {uid}")
                    user_id, user = buscar_usuario_por_uid(uid)
                    if user:
                        nombre = user.get('usuario_nombre', 'Sin nombre')
                        print(f"[DB] Usuario: {nombre}")

                        with lock:
                            if material_detectado:
                                puntos = 20 if material_detectado == "plastico" else 30
                                puntos_actuales = user.get("usuario_puntos", 0)
                                nuevos_puntos = puntos_actuales + puntos
                                usuarios_ref.child(user_id).update({"usuario_puntos": nuevos_puntos})
                                print(f"[DB] +{puntos} puntos por {material_detectado}. Total: {nuevos_puntos}")

                                # Crear efecto de partículas para éxito
                                create_particles(320, 240, COLORS['success'], 30)

                                material_detectado = None  # desbloqueo
                    else:
                        print("[DB] UID no registrado")
                    last_uid = uid
            else:
                last_uid = None
            time.sleep(0.5)
        except (NoCardException, CardConnectionException):
            last_uid = None
            time.sleep(0.5)
        except Exception as e:
            print(f"[NFC ERROR] {e}")
            last_uid = None
            time.sleep(1)


# ---------- YOLO + INTERFAZ MEJORADA ----------
def loop_yolo():
    global material_detectado, animation_time, pulse_alpha, wave_radius
    weights = Path("modelo/best.onnx")
    if not weights.exists():
        raise FileNotFoundError(f"No se encontró {weights.resolve()}")

    model = YOLO(str(weights))
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    prev = time.time()

    # control de detección sostenida
    deteccion_activa = None
    inicio_deteccion = None
    bloqueo_inicio = None
    mostrando_procesando = False

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        animation_time = time.time()

        # Crear overlay para efectos
        overlay = frame.copy()

        with lock:
            if material_detectado is None:
                # --- Normal: cámara con YOLO ---
                results = model.predict(frame, conf=0.5, imgsz=320, verbose=False)
                annotated = results[0].plot()

                clase_detectada = None
                detection_boxes = []

                for r in results:
                    for box in r.boxes:
                        cls_id = int(box.cls[0])
                        class_name = model.names[cls_id]
                        if class_name in ["plastico", "aluminio"]:
                            clase_detectada = class_name
                            # Obtener coordenadas de la caja
                            x1, y1, x2, y2 = map(int, box.xyxy[0])
                            detection_boxes.append((x1, y1, x2, y2, class_name))

                # Dibujar cajas de detección mejoradas
                for x1, y1, x2, y2, class_name in detection_boxes:
                    color = COLORS.get(class_name, COLORS['primary'])

                    # Efecto pulsante en la caja
                    pulse = (math.sin(animation_time * 3) + 1) / 2
                    thickness = int(2 + pulse * 2)

                    cv2.rectangle(annotated, (x1, y1), (x2, y2), color, thickness)

                    # Esquinas animadas
                    corner_size = 20
                    cv2.line(annotated, (x1, y1), (x1 + corner_size, y1), color, thickness + 2)
                    cv2.line(annotated, (x1, y1), (x1, y1 + corner_size), color, thickness + 2)
                    cv2.line(annotated, (x2, y1), (x2 - corner_size, y1), color, thickness + 2)
                    cv2.line(annotated, (x2, y1), (x2, y1 + corner_size), color, thickness + 2)
                    cv2.line(annotated, (x1, y2), (x1 + corner_size, y2), color, thickness + 2)
                    cv2.line(annotated, (x1, y2), (x1, y2 - corner_size), color, thickness + 2)
                    cv2.line(annotated, (x2, y2), (x2 - corner_size, y2), color, thickness + 2)
                    cv2.line(annotated, (x2, y2), (x2, y2 - corner_size), color, thickness + 2)

                # lógica de temporizador
                if clase_detectada:
                    if deteccion_activa == clase_detectada:
                        # sigue el mismo objeto
                        if time.time() - inicio_deteccion >= 5:  # 5 segundos
                            material_detectado = clase_detectada
                            bloqueo_inicio = time.time()
                            mostrando_procesando = True
                            print(f"[YOLO] {clase_detectada} detectado por 5s. Bloqueando...")
                            client.publish(MQTT_MATERIAL_TOPIC, clase_detectada, qos=1)
                    else:
                        # nuevo objeto detectado
                        deteccion_activa = clase_detectada
                        inicio_deteccion = time.time()
                else:
                    # si no hay detección, reset
                    deteccion_activa = None
                    inicio_deteccion = None

                # Mostrar FPS con estilo mejorado
                now = time.time()
                fps = 1 / (now - prev)
                prev = now

                # Panel de información superior
                cv2.rectangle(annotated, (0, 0), (640, 80), (0, 0, 0, 180), -1)
                draw_floating_text(annotated, f"FPS: {fps:.1f}", 20, 30, 0.7, COLORS['accent'])
                draw_floating_text(annotated, "RECICLAJE INTELIGENTE", 180, 30, 0.9, COLORS['primary'])

                # mostrar overlay del tiempo si hay detección
                if deteccion_activa and inicio_deteccion:
                    tiempo = time.time() - inicio_deteccion
                    progreso = min(tiempo / 5.0, 1.0)

                    # Panel de progreso
                    cv2.rectangle(annotated, (50, 400), (590, 460), (0, 0, 0, 200), -1)

                    material_color = COLORS.get(deteccion_activa, COLORS['primary'])
                    draw_floating_text(annotated, f"Detectando {deteccion_activa.upper()}", 70, 430, 0.8,
                                       material_color)
                    draw_progress_bar(annotated, progreso, 70, 440, 500, 15, material_color)

                # Borde animado
                draw_animated_border(annotated)

                # Actualizar partículas
                update_particles(annotated)

                cv2.imshow("Reciclaje Inteligente", annotated)

            else:
                # --- Bloqueo: pantalla con diseño profesional ---
                # Crear fondo con gradiente
                pantalla = create_gradient_background(480, 640, COLORS['dark'], (20, 20, 40))

                if mostrando_procesando:
                    # Título
                    draw_floating_text(pantalla, "PROCESANDO", 200, 150, 1.5, COLORS['accent'])

                    # Spinner de carga
                    draw_loading_spinner(pantalla, 320, 200, 40, COLORS['primary'])

                    # Círculo pulsante
                    draw_pulsing_circle(pantalla, 320, 200, 80, COLORS['primary'])

                    # Mensaje
                    draw_floating_text(pantalla, "Tu solicitud esta siendo procesada...", 120, 280, 0.8,
                                       COLORS['white'])

                    if time.time() - bloqueo_inicio > 2:  # 2s luego cambia mensaje
                        mostrando_procesando = False
                else:
                    # Título
                    draw_floating_text(pantalla, "ACERCA TU TARJETA", 150, 150, 1.2, COLORS['success'])

                    # Ícono NFC (círculos concéntricos animados)
                    for i in range(3):
                        time_offset = i * 0.5
                        radius = 30 + i * 20 + int(10 * math.sin(animation_time * 2 + time_offset))
                        alpha = 0.3 + 0.4 * math.sin(animation_time * 2 + time_offset)
                        color = tuple(int(c * alpha) for c in COLORS['primary'])
                        cv2.circle(pantalla, (320, 240), radius, color, 3)

                    # Punto central
                    cv2.circle(pantalla, (320, 240), 8, COLORS['accent'], -1)

                    # Mensaje
                    draw_floating_text(pantalla, "al lector NFC para completar", 170, 350, 0.8, COLORS['white'])

                    # Ondas de conexión
                    wave_radius = (wave_radius + 2) % 100
                    for r in range(0, 100, 25):
                        alpha = 1.0 - (r + wave_radius) / 100
                        if alpha > 0:
                            color = tuple(int(c * alpha * 0.3) for c in COLORS['success'])
                            cv2.circle(pantalla, (320, 240), r + wave_radius, color, 2)

                # Borde animado
                draw_animated_border(pantalla, 4, COLORS['accent'])

                # Actualizar partículas
                update_particles(pantalla)

                cv2.imshow("Reciclaje Inteligente", pantalla)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


# ---------- MAIN ----------
if __name__ == "__main__":
    threading.Thread(target=loop_nfc, daemon=True).start()
    loop_yolo()