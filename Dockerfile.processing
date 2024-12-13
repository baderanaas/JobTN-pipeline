# Use a lightweight Python 3.10 base image
FROM python:3.10-slim

# Set a working directory in the container
WORKDIR /app

# Copy the current directory's contents into the container
COPY . /app

# Install any required dependencies (if you have a requirements.txt)
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the Python script into the container
COPY processing_stream.py .

# Command to run the script
CMD ["python", "processing_stream.py"]
