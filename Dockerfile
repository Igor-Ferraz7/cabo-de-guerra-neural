# Imagem para publicar no Hugging Face Spaces (CPU).
# Leia o README antes: a inferência fica mais lenta que no notebook.
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# torch na versão CPU: a versão padrão arrasta ~2 GB de CUDA sem necessidade
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY jogo/ ./jogo/
COPY web/ ./web/

ENV YOLO_CONFIG_DIR=/tmp/Ultralytics
EXPOSE 7860
CMD ["python", "jogo/servidor.py", "--host", "0.0.0.0", "--porta", "7860", "--imgsz", "384"]
