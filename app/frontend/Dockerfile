# Use Python base image with platform specification
FROM --platform=linux/amd64 python:3.10-slim

# Set working directory
WORKDIR /frontend

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .


# Command to run the application
CMD ["gradio", "ui.py"]