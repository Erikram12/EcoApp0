# App0 - Reciclaje Inteligente

Este proyecto usa cámara (OpenCV), un modelo YOLO exportado a ONNX (Ultralytics) para detectar `plastico` y `aluminio`, lector NFC (pyscard) y publica eventos por MQTT. Además, se conecta a Firebase Realtime Database.

## Requisitos del sistema
- Raspberry Pi 4 (recomendado) con Raspberry Pi OS 64-bit.
- Cámara compatible con OpenCV (USB o cámara oficial).
- Lector NFC compatible PC/SC.
- Python 3.9 o 3.10.
- Acceso a Internet para MQTT y Firebase.

## Paquetes del sistema (Raspberry Pi)
Ejecuta en tu Raspberry Pi:
```bash
sudo apt update
sudo apt install -y python3-venv python3-dev libatlas-base-dev \
    pcscd pcsc-tools libpcsclite-dev libcap-dev
# Opcional: utilidades multimedia si usas interfaz gráfica
sudo apt install -y libgtk-3-0
# Activa el servicio PC/SC para el lector NFC
sudo systemctl enable pcscd --now
```

## Preparar entorno Python
```bash
# En la Raspberry Pi, dentro de la carpeta del proyecto
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Notas importantes:
- Si te falla `opencv-python` en Raspberry Pi sin entorno gráfico, puedes usar la variante sin GUI:
  ```bash
  pip uninstall -y opencv-python && pip install opencv-python-headless
  ```
- Ultralytics puede intentar instalar PyTorch. En Raspberry Pi 64-bit puedes instalar CPU wheels oficiales:
  ```bash
  pip install --index-url https://download.pytorch.org/whl/cpu torch torchvision --only-binary :all:
  ```
  Si no necesitas entrenar (solo inferencia ONNX), el backend principal lo hace `onnxruntime`, pero Ultralytics puede requerir `torch` para importar el paquete. Si tienes problemas, instala las ruedas anteriores.
- Para `pyscard`, ya instalamos `pcscd` y `libpcsclite-dev` con `apt` (requisito del sistema).

## Variables y credenciales
Configura tus credenciales/URLs de forma segura. En `app.py` hay variables de entorno para MQTT y rutas de Firebase:
- MQTT: `MQTT_BROKER`, `MQTT_PORT`, `MQTT_USER`, `MQTT_PASSWORD`, `MQTT_MATERIAL_TOPIC`.
- Firebase: en `config/` hay un JSON de clave de servicio. No lo subas a GitHub.

Puedes crear un archivo `.env` y exportarlas antes de ejecutar, o configurarlas en tu servicio systemd.

## Archivos clave
- Modelo ONNX: `modelo/best.onnx`
- Configuración Firebase: `config/*.json` (clave de servicio)
- Código principal: `app.py`

## Ejecutar la aplicación
Asegúrate de que tu cámara está conectada y el servicio PC/SC activo:
```bash
source .venv/bin/activate
python app.py
```
- Ventana: pulsa `q` para salir.
- El hilo NFC se inicia en paralelo y otorga puntos cuando detecta una tarjeta después de una detección válida.

## Solución de problemas
- Cámara no abre: verifica `ls /dev/video*` y permisos; prueba con `v4l2-ctl --list-devices`.
- OpenCV falla en GUI: usa `opencv-python-headless` si no tienes entorno gráfico, pero `cv2.imshow` no funcionará; ejecuta con GUI o adapta el código.
- Lector NFC: verifica `pcsc_scan` y que `pcscd` esté activo.
- ONNX Runtime: si hay error de librerías, asegúrate de estar en 64-bit y Python 3.9/3.10.

## Subir el proyecto a GitHub
1. Inicia el repositorio (solo la primera vez):
   ```bash
   git init
   git branch -M main
   git add .
   git commit -m "Inicial: App0"
   ```
2. Crea un repositorio nuevo en GitHub (desde la web) sin README inicial.
3. Agrega el remoto y sube:
   ```bash
   git remote add origin https://github.com/TU_USUARIO/TU_REPO.git
   git push -u origin main
   ```

Consejos de seguridad:
- No subas `config/*.json` (clave de servicio), credenciales ni archivos enormes. Este repo incluye un `.gitignore` para ayudarte.
- Si necesitas versionar `modelo/best.onnx` (archivos grandes), considera Git LFS:
  ```bash
  git lfs install
  git lfs track "modelo/*.onnx"
  git add .gitattributes
  git commit -m "Track ONNX con LFS"
  ```

## Estructura sugerida del proyecto
```
App0/
├─ app.py
├─ requirements.txt
├─ README.md
├─ .gitignore
├─ config/
│  └─ resiclaje-39011-firebase-adminsdk-....json  # (no subir)
├─ modelo/
│  └─ best.onnx
└─ sounds/
   ├─ plastico1.mp3
   └─ aluminio1.mp3
```

## Licencia
Define la licencia de tu preferencia (MIT, Apache-2.0, etc.).
