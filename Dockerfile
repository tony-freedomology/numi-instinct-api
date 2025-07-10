# Start with an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Set environment variables to prevent Python from writing .pyc files to disc and to keep output unbuffered
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies that might be needed (though for this app, likely not many)
# RUN apt-get update && apt-get install -y --no-install-recommends some-package && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# --no-cache-dir: Disables the pip cache, which can reduce image size.
# --upgrade pip: Ensures pip itself is up to date.
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's source code into the container at /app
# This includes main.py, models.py, scoring_engine.py, config.py, data_loader.py, profile_store.py
# and the data/ directory. The . in COPY . . refers to the build context (your project root) 
# and the current WORKDIR in the container (/app).
COPY . .

# Make port 8000 available to the world outside this container
# This doesn't actually publish the port but documents that the app inside listens on this port.
# The actual port mapping happens when you run the container or configure the hosting service.
EXPOSE 8000

# Define the command to run your app using Gunicorn. This is the command that will be run when the container starts.
# Gunicorn is a production-grade WSGI server.
# -w 2: Number of worker processes. A common starting point is 2 * (number of CPU cores) + 1. Adjust based on your needs and server specs.
# -k uvicorn.workers.UvicornWorker: Use Uvicorn workers, which are ASGI compatible and ideal for FastAPI.
# main:app: The FastAPI application instance (the 'app' variable in your 'main.py' file).
# --bind 0.0.0.0:8000: Gunicorn will listen on port 8000 on all available network interfaces within the container.
CMD ["gunicorn", "-w", "2", "-k", "uvicorn.workers.UvicornWorker", "main:app", "--bind", "0.0.0.0:8000"] 