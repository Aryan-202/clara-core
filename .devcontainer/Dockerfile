# Use Python 3.14 with uv pre-installed
FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Set up Python environment
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_SYSTEM_PYTHON=1

# Copy dependency files first (for better caching)
COPY pyproject.toml setup.py README.md ./

# Install project dependencies using uv
RUN uv pip install --system \
    -e . \
    black \
    flake8 \
    mypy \
    isort \
    pytest \
    pytest-cov \
    ipython

# Create a non-root user
RUN useradd -m -u 1000 vscode && \
    chown -R vscode:vscode /workspaces/clara-core

USER vscode

# Set working directory
WORKDIR /workspaces/clara-core