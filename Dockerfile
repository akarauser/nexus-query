FROM python:3.12-slim

WORKDIR /nexus-query

RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates libgl1 libglib2.0-0

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY . /nexus-query

RUN uv sync --locked

EXPOSE 8000 8501

CMD ["sh", "-c", "uv run uvicorn nexus_query.scripts.api_server:app --host 0.0.0.0 --port 8000 & uv run streamlit run nexus_query/app.py --server.port 8501 --server.address 0.0.0.0"]

HEALTHCHECK --interval=1m --timeout=3s \
  CMD curl -f http://localhost:8501/_stcore/health || exit 1