# Dockerfile pour GEO/GSO Pipeline
# Multi-stage build pour optimiser la taille de l'image

# Stage 1: Builder
FROM python:3.11-slim as builder

# Éviter prompts interactifs
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Installer dépendances de build
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Créer et utiliser un utilisateur non-root
RUN useradd -m -u 1000 -s /bin/bash pipeline

WORKDIR /tmp

# Copier requirements
COPY requirements.txt .

# Installer dépendances Python dans un venv
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Pré-télécharger les modèles
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Stage 2: Runtime
FROM python:3.11-slim

# Variables d'environnement
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# Installer seulement les dépendances runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Créer utilisateur non-root
RUN useradd -m -u 1000 -s /bin/bash pipeline && \
    mkdir -p /app /data/out && \
    chown -R pipeline:pipeline /app /data

# Copier venv depuis builder
COPY --from=builder --chown=pipeline:pipeline /opt/venv /opt/venv

# Copier cache des modèles
COPY --from=builder --chown=pipeline:pipeline /root/.cache /home/pipeline/.cache

WORKDIR /app

# Copier le code source
COPY --chown=pipeline:pipeline . .

# Switch to non-root user
USER pipeline

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Volume pour les outputs
VOLUME ["/data/out"]

# Entry point
ENTRYPOINT ["python", "generate.py"]
CMD ["--input", "topics.json", "--output", "/data/out"]

# Metadata
LABEL maintainer="contact@example.com" \
      version="1.0.0" \
      description="GEO/GSO Article Generation Pipeline"
