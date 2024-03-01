# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container to /app
WORKDIR /app

# Copy just the requirements.txt file and install dependencies
# to leverage Docker cache
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# After installing dependencies, copy the entire project
# This step is after the dependency installation to leverage caching
COPY . .

# Expose the port your app runs on
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=src/app.py
ENV NAME=UniFeeTracker
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

#  Command to run the Flask application using Gunicorn 
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]