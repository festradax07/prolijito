# syntax=docker/dockerfile:1
# Imagen única de prolijito: la usan la CLI (scripts/install.sh) y la GitHub Action (action.yml).
ARG PYTHON_IMAGE=python:3.12-slim@sha256:a6e34c598f2467ed0e9a8d349809fcd8b5c603269512df273a0bb1784edc11b1

# ---------- build: instala el paquete en un venv (solo wheels, sin compiladores) ----------
FROM ${PYTHON_IMAGE} AS build
WORKDIR /src
COPY pyproject.toml README.md LICENSE NOTICE.md ./
COPY src ./src
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir --disable-pip-version-check .

# ---------- final ----------
FROM ${PYTHON_IMAGE}
LABEL org.opencontainers.image.title="prolijito" \
      org.opencontainers.image.description="Valida el formato de informes contra una norma, sin tocar el contenido." \
      org.opencontainers.image.source="https://github.com/festradax07/prolijito" \
      org.opencontainers.image.licenses="AGPL-3.0-or-later"

# poppler mide el PDF; las fuentes quedan fijas para que el render no dependa de la máquina.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       poppler-utils fonts-liberation fonts-linuxlibertine fontconfig \
    && rm -rf /var/lib/apt/lists/* \
    && fc-cache -f

COPY --from=build /opt/venv /opt/venv
COPY profiles /opt/prolijito/profiles
COPY scripts/action-entrypoint.sh /usr/local/bin/prolijito-action

ENV PATH="/opt/venv/bin:${PATH}" \
    PROLIJITO_PROFILES_DIR=/opt/prolijito/profiles \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    XDG_CACHE_HOME=/tmp/.cache

# Sin USER: GitHub exige root en las container actions. La CLI corre con el usuario del host
# (`docker run -u`, ver scripts/install.sh). ADR 0007.
WORKDIR /work
ENTRYPOINT ["prolijito"]
