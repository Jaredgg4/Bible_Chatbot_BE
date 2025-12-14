FROM python:3.12-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Copy application code
COPY app.py ./

EXPOSE 4000

# Use Gunicorn as production WSGI server
CMD gunicorn --bind 0.0.0.0:${PORT:-4000} --workers 2 --threads 2 app:app
