FROM python:3.10-slim

# 2) Set a working directory
WORKDIR /app
# 4) Copy only requirements first (for better caching)
COPY requirements.txt .

# 5) Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 6) Copy the rest of your application
COPY . .

# 7) Ensure the app listens on the port Cloud Run expects
ENV PORT=8080

# 8) Expose the port (optional, for documentation)
EXPOSE 8080

ENV LOCATION="us-central1"
ENV PROJECT="365383383851"
ENV GOOGLE_CLOUD_PROJECT="pivotal-keep-461818-j4"

# 9) Run Uvicorn when the container starts
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]