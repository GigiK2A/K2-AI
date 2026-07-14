FROM python:3.12-slim

WORKDIR /app

# ca-certificates + curl (TLS verso la tailnet/DERP). Tailscale userspace: binari
# statici dall'immagine ufficiale, avviati SOLO se TS_AUTHKEY è impostata a runtime
# (vedi seed_and_run.sh). Senza TS_AUTHKEY restano inerti → deploy invariato.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*
COPY --from=tailscale/tailscale:stable /usr/local/bin/tailscaled /usr/local/bin/tailscaled
COPY --from=tailscale/tailscale:stable /usr/local/bin/tailscale  /usr/local/bin/tailscale

# Dipendenze (reportlab non richiede apt extra: usa font Type1 built-in).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV K2A_8E_OUT_DIR=/tmp/8e-out
EXPOSE 8800

# Railway inietta $PORT; default 8800 in locale.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8800}"]
