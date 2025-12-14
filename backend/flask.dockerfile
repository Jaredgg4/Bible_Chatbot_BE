FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY . .

EXPOSE 4000

# Use shell form to allow environment variable expansion
CMD flask run --host 0.0.0.0 --port ${PORT:-4000}
