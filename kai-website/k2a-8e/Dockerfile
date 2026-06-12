FROM python:3.12-slim

WORKDIR /app

# Dipendenze (reportlab non richiede apt extra: usa font Type1 built-in).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV K2A_8E_OUT_DIR=/tmp/8e-out
EXPOSE 8800

# Railway inietta $PORT; default 8800 in locale.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8800}"]
