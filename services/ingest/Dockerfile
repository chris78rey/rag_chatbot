FROM python:3.11-slim

WORKDIR /workspace

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements (placeholder)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt || echo "requirements.txt no encontrado"

# Copiar código
COPY . .

# Comando por defecto (será overridden en docker-compose)
CMD ["sleep", "infinity"]