FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY tests/ ./tests/
COPY README.md .

ENV DRY_RUN=true
ENV MAX_SPEND_SOL=0.05

CMD ["python", "-m", "src.measure"]
