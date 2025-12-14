FROM python:3.12-slim

WORKDIR /app

# Copy requirements and install dependencies from backend folder
COPY backend/requirements.txt ./
RUN pip install -r requirements.txt

# Copy application code from backend folder
COPY backend/app.py ./

EXPOSE 4000

# Use Gunicorn as production WSGI server with increased timeout
CMD gunicorn --bind 0.0.0.0:${PORT:-4000} --workers 2 --threads 2 --timeout 120 --access-logfile - --error-logfile - app:app
