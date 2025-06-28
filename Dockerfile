# Install uv
FROM python:3.12-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set environment variables for builder
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production
ENV DATABASE_URL=sqlite:///./app.db

# Install build dependencies
RUN apt-get update && apt-get install -y \
    libmagic1 \
    libpq-dev \
    gcc \
    curl \
    python3-dev \
    wget \
    unzip \
    openjdk-17-jdk \
    && rm -rf /var/lib/apt/lists/*

# Change the working directory to the `app` directory
WORKDIR /app

# Copy project files first to ensure lock file is available
COPY uv.lock pyproject.toml ./

# Install dependencies - try locked first, fallback to unlocked if needed
RUN --mount=type=cache,target=/root/.cache/uv \
    (uv sync --locked --no-install-project --no-editable || \
     uv sync --no-install-project --no-editable)

# Copy the project into the intermediate image
ADD . /app

# Sync the project - try locked first, fallback to unlocked if needed
RUN --mount=type=cache,target=/root/.cache/uv \
    (uv sync --locked --no-editable || \
     uv sync --no-editable)

FROM python:3.12-slim

# Set environment variables for JMeter
ENV JMETER_VERSION=5.6.3
ENV JMETER_HOME=/opt/apache-jmeter-${JMETER_VERSION}
ENV PATH="${JMETER_HOME}/bin:/app/.venv/bin:$PATH"

# Set application environment variables
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production
ENV DATABASE_URL=sqlite:///./app.db

# Install runtime dependencies including JMeter requirements
RUN apt-get update && apt-get install -y \
    libmagic1 \
    libpq-dev \
    curl \
    wget \
    unzip \
    openjdk-17-jdk \
    && rm -rf /var/lib/apt/lists/*

# Install JMeter
RUN wget https://archive.apache.org/dist/jmeter/binaries/apache-jmeter-${JMETER_VERSION}.tgz \
    && tar -xzf apache-jmeter-${JMETER_VERSION}.tgz -C /opt \
    && rm apache-jmeter-${JMETER_VERSION}.tgz \
    && chmod +x ${JMETER_HOME}/bin/jmeter

# Copy the environment with all dependencies
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app /app
# Copy uv binary for package management in runtime
COPY --from=builder /bin/uv /bin/uv

# Set working directory
WORKDIR /app

# Create required directories
RUN mkdir -p jmx_files jtl_files reports static templates

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser \
    && chown -R appuser:appuser /app

USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -s http://localhost:8000/health || exit 1

# Start application
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
