FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml ./
COPY src/ ./src/

RUN pip install --no-cache-dir .

EXPOSE 9000

CMD ["python", "-c", "import os, uvicorn; uvicorn.run('sage_mcp.server:app', host='0.0.0.0', port=int(os.environ.get('PORT', '9000')))"]
