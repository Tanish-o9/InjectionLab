FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependencies list
COPY requirements.txt pyproject.toml ./

# Install python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Generate attack dataset and train injection detector
RUN python -m attacks.build_attacks && \
    python -m defenses.detector

# Expose Streamlit default port
EXPOSE 8501

# Healthcheck
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Launch Streamlit web playground
ENTRYPOINT ["streamlit", "run", "demo.py", "--server.port=8501", "--server.address=0.0.0.0"]
