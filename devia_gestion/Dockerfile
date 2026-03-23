# Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    # LaTeX minimal + français
    texlive-latex-base \
    texlive-latex-recommended \
    texlive-fonts-recommended \
    texlive-lang-french \
    # Outils requis pour pdflatex
    texlive-latex-extra \
    fonts-dejavu-core \
    ghostscript \
    dvipdfmx \
    texlive-fonts-extra \
    && rm -rf /var/lib/apt/lists/*

# Installer les dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Créer un utilisateur non-root
RUN adduser --disabled-password --gecos '' appuser && chown -R appuser:appuser /app
USER appuser


# Copier TOUT le code (y compris start.sh)
COPY --chown=appuser:appuser . .

# → PAS de collectstatic ici !
# → On le fera dans start.sh au démarrage

ENV PYTHONPATH=/app

CMD ["./start.sh"]