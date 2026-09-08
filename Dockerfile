# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies for OCR
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-hin \
    && rm -rf /var/lib/apt/lists/*

# Copy the entire repository to working directory
COPY . .

# Install the Python dependencies
RUN pip install --no-cache-dir -r backend/requirements.txt

# Expose the port FastAPI will run on
EXPOSE $PORT

# Define the command to run your FastAPI application
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "$PORT"]