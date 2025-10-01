# Usa la imagen arm64 oficial de Ultralytics (Debian 12 + Python3)
FROM ultralytics/ultralytics:latest-arm64

# Paquetes del sistema necesarios para OpenCV GUI, cámara y PC/SC (NFC)
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 libgtk-3-0 \
    v4l-utils usbutils \
    pcscd pcsc-tools libpcsclite1 \
    && rm -rf /var/lib/apt/lists/*

# Dependencias Python que usas
# Nota: ultralytics ya viene, pero añadimos onnx/onnxruntime por si usas ONNX directo,
# firebase_admin, paho-mqtt, pyscard, opencv (normalmente ya viene, lo reforzamos)
RUN pip install --no-cache-dir \
    onnx onnxruntime \
    firebase_admin paho-mqtt pyscard \
    opencv-python

# Copiamos el proyecto
WORKDIR /app
COPY . /app

# Arranca el demonio PC/SC dentro del contenedor para el lector NFC
# y luego ejecuta tu app
CMD ["/bin/bash", "-lc", "service pcscd start && python app.py"]
