# Turkey HSD Analyzer v2.0
# Production Docker Image

FROM python:3.11-slim

LABEL maintainer="Turkey HSD Analyzer Team"
LABEL version="2.0.0"
LABEL description="Advanced ANOVA & Mean Separation Analysis Platform"

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy requirements first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app.py .
COPY modules/ modules/
COPY .streamlit/ .streamlit/

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl --fail http://localhost:8501/_stcore/health || exit 1

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
