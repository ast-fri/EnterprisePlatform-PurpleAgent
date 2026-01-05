FROM ghcr.io/astral-sh/uv:python3.13-bookworm

RUN apt-get update && apt-get install -y git curl && rm -rf /var/lib/apt/lists/*

RUN adduser agent
USER agent
WORKDIR /home/agent

COPY --chown=agent:agent pyproject.toml uv.lock README.md ./
COPY --chown=agent:agent src src

RUN \
    --mount=type=cache,target=/home/agent/.cache/uv,uid=1000 \
    uv sync --locked

ENV PYTHONUNBUFFERED=1
ENV AZURE_OPENAI_API_KEY=""
ENV AZURE_OPENAI_ENDPOINT=""
ENV AZURE_OPENAI_DEPLOYMENT="gpt-4o"
ENV AZURE_OPENAI_API_VERSION="2024-02-01"

ENTRYPOINT ["uv", "run", "src/server.py"]
CMD ["--host", "0.0.0.0", "--port", "9002"]
EXPOSE 9002
