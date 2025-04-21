# Use official Python image as base
FROM python:3.11-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    unzip \
    gnupg \
    libnss3 \
    libxss1 \
    libasound2 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libgtk-3-0 \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Install Playwright and Python dependencies
RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install -r requirements.txt

# Install Playwright browsers (including Chromium)
RUN apt-get update && apt-get install -y libcurl4 openssh-client && \
    pip install playwright && \
    playwright install chromium

# Add app code
COPY . /app
WORKDIR /app

# Expose port for gunicorn
EXPOSE 10000

# Start the app
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:10000"]
