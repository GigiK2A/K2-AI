FROM n8nio/n8n:2.18.5
EXPOSE 5678
# Upstream n8nio/n8n already sets USER node internally; re-state explicitly
# so static scanners (semgrep dockerfile.security.missing-user) detect it.
USER node
CMD ["sh", "-c", "n8n start --host 0.0.0.0 --port ${PORT:-5678}"]
