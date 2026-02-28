FROM python:3.11-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
COPY src/ src/

RUN uv sync --frozen --no-dev

ENV MCP_TRANSPORT=sse
ENV MCP_HOST=0.0.0.0
EXPOSE 8000

CMD ["uv", "run", "berlin-opendata-mcp"]
