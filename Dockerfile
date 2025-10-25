FROM python:3.12-slim-bookworm          # Base OS with Python

# Creates 'wagtail' user (non-root for security)
RUN useradd --create-home --shell /bin/bash wagtail

WORKDIR /app                            # All commands run from here

ENV PYTHONUNBUFFERED=1                  # Real-time logs
ENV PORT=8080                           # Cloud Run default port

# Installs: gcc, PostgreSQL dev libs, image processing libs
RUN apt-get install build-essential libpq-dev libjpeg62-turbo-dev

# Installs: Django, Wagtail, psycopg2, gunicorn, etc.
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copies your Django app code
COPY . .

# Creates /tmp/certs directory (writable by wagtail user)
RUN mkdir -p /tmp/certs && chown wagtail:wagtail /tmp/certs

# Makes scripts executable
COPY entrypoint.sh start.sh ./
RUN chmod +x ./entrypoint.sh ./start.sh

USER wagtail                            # Switch to non-root user

EXPOSE 8080                             # Port for HTTP traffic

ENTRYPOINT ["./entrypoint.sh"]          # First script to run