FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot files
COPY polymarket_bot_pro.py .

# Run the bot
CMD ["python", "polymarket_bot_pro.py"]
