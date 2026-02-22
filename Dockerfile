FROM python:3.12-slim

# Hugging Face Spaces requires port 7860
ENV PORT=7860

WORKDIR /app

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files first for Docker layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies (no dev deps in production)
RUN uv sync --frozen --no-dev --no-cache

# Copy application code
COPY app/ app/
COPY main.py .
COPY alembic.ini .

# Expose the HF Spaces port
EXPOSE 7860

# Run with uvicorn on port 7860
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
