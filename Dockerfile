FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run DB init if needed, then start gunicorn
CMD ["sh", "-c", "python db_init.py && gunicorn -w 4 -b 0.0.0.0:5101 app:app"]
