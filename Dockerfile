# Stage 1: Builder
FROM python:3.13-bookworm AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy dependency files first for caching
COPY pyproject.toml uv.lock ./

# Install dependencies (without the project itself)
RUN uv sync --frozen --no-install-project

# Copy source
COPY src ./src

# Install the project
RUN uv sync --frozen

# Stage 2: Runtime
FROM python:3.13-slim-bookworm

# Create non-root user
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid 1000 --shell /bin/bash appuser

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Set PATH to use venv
ENV PATH="/app/.venv/bin:$PATH"

# Install awscli (needed at runtime)
RUN pip install --no-cache-dir awscli==1.35.20

USER appuser

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD ["crystalia-collector", "--help"]

ENTRYPOINT ["crystalia-collector"]
