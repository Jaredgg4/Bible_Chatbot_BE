FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY . .

EXPOSE 4000

# Use Gunicorn as production WSGI server
CMD gunicorn --bind 0.0.0.0:${PORT:-4000} --workers 2 --threads 2 app:app
