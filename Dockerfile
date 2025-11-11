# Use official Playwright Python base image (includes framework, browsers installed separately)
FROM mcr.microsoft.com/playwright/python:v1.48.0-noble

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (CRITICAL: Required for PDF/PPTX generation)
RUN playwright install --with-deps chromium

# Copy entrypoint script first
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8010

# Expose port (Railway will override with $PORT)
EXPOSE 8010

# Use entrypoint script to handle PORT variable properly
ENTRYPOINT ["/app/entrypoint.sh"]
