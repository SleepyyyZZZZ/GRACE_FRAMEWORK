FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Verify environment on build
RUN python test_lib.py

# Default: run tests
CMD ["python", "-m", "pytest", "tests/", "-s", "-v"]
