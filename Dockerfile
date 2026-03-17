FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml ./
COPY src/ ./src/

RUN pip install --no-cache-dir .

EXPOSE 9000

CMD uvicorn sage_mcp.server:app --host 0.0.0.0 --port ${PORT:-9000}
