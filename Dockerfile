# Simple, secure Python container that runs as a non-root user on port 8080
FROM python:3.11-slim

ARG VCS_REF=dev
ARG VCS_URL=https://example.com/repo

LABEL org.opencontainers.image.revision=$VCS_REF \
      org.opencontainers.image.source=$VCS_URL

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY app/ /app/
RUN pip install --no-cache-dir -r /app/requirements.txt \
    && useradd -u 1001 -r -s /sbin/nologin appuser

USER 1001
EXPOSE 8080
ENTRYPOINT ["python", "/app/app.py"]



