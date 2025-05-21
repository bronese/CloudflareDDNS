
FROM python:3.11-slim AS base
ENV TZ=America/Toronto
ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt
COPY . .
CMD [ "python3", "-u", "./DDNS-update.py" ]
