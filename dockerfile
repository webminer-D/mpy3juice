# Use a smaller base image (alpine) with Python installed
FROM python:3.9-alpine

# Set the working directory in the container
WORKDIR /app

# Install system dependencies (ffmpeg) and remove cache to reduce image size
RUN apk add --no-cache ffmpeg && \
    pip install --no-cache-dir --upgrade pip

# Copy only the necessary files into the container at /app
COPY msc.py requirements.txt /app/

# Install Python dependencies without cache to minimize size
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 8000 for FastAPI
EXPOSE 8050

# Define environment variable (optional, for FastAPI)
ENV PYTHONPATH=/app

# Run FastAPI with uvicorn
CMD ["uvicorn", "msc:app", "--host", "0.0.0.0", "--port", "8050"]
