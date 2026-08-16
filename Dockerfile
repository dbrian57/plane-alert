FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY plane_alert ./plane_alert

CMD ["python", "-m", "plane_alert.main"]
