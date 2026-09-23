FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends docker.io && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir fastapi==0.141.1 uvicorn==0.53.0
WORKDIR /worker
COPY runner/service.py .
CMD ["uvicorn", "service:app", "--host", "0.0.0.0", "--port", "8090"]
