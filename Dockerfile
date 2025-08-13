# Use a lightweight Python base image
FROM python:3.11-slim

# Set environment vars
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the app code
COPY . .

# Expose the port Render will use
EXPOSE 5000

# Run with Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
