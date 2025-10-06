# Bunny AI - Universal Docker Container
# Supports: x86_64, ARM64 (Apple Silicon, ARM servers)

FROM ubuntu:22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV BUNNY_HOME=/app/.bunny
ENV PATH="/app/.bunny/llama.cpp/build/bin:${PATH}"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    cmake \
    build-essential \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy project files
COPY . /app/

# Create virtual environment and install dependencies
RUN python3 -m venv /app/venv
RUN /app/venv/bin/pip install --upgrade pip
RUN /app/venv/bin/pip install huggingface-hub>=0.20.0 click>=8.1.0 requests>=2.28.0 fastapi uvicorn python-multipart

# Install Bunny package
RUN /app/venv/bin/pip install -e .

# Build llama.cpp
RUN git clone https://github.com/ggerganov/llama.cpp.git /app/llama.cpp
WORKDIR /app/llama.cpp
RUN mkdir build && cd build && \
    cmake .. -DCMAKE_BUILD_TYPE=Release && \
    make -j$(nproc)

# Create models directory
RUN mkdir -p /app/.bunny/models

# Create startup script
RUN echo '#!/bin/bash\n\
set -e\n\
echo "=== Bunny AI Docker Container ==="\n\
echo "Starting Bunny AI..."\n\
cd /app\n\
source venv/bin/activate\n\
\n\
# Start web UI on all interfaces\n\
echo "Starting web UI on port 8080..."\n\
exec b serve_ui --host 0.0.0.0 --port 8080\n\
' > /app/start.sh && chmod +x /app/start.sh

# Expose ports
EXPOSE 8080

# Set working directory back to app
WORKDIR /app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/api/server/status || exit 1

# Start the application
CMD ["/app/start.sh"]
