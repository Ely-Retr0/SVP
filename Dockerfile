FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    nmap \
    tcpdump \
    aircrack-ng \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000
CMD ["python", "svp.py", "--interface", "eth0", "--scan-range", "10.3.141.0/24"]
