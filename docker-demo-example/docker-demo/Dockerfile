# Start from an existing image that already has Python
FROM python:3.12-slim

# Work inside /app in the container
WORKDIR /app

# Install libraries first (Docker caches this step)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the code in
COPY . .

# Document the port and set the default command
EXPOSE 8000
CMD ["python", "app.py"]
