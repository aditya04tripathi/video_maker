FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    ffmpeg \
    imagemagick \
    && rm -rf /var/lib/apt/lists/*

RUN find /etc -name "policy.xml" -exec sed -i 's/none/read,write/g' {} +

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run the scheduling script directly
CMD ["python", "scripts/scheduled_reel_post.py"]
