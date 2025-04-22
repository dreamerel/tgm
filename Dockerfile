FROM python:3.9-slim

WORKDIR /app

COPY requirements-prod.txt ./
RUN pip install --no-cache-dir -r requirements-prod.txt

COPY . .

ENV FLASK_APP=main.py
ENV FLASK_ENV=production
ENV PORT=5000

EXPOSE $PORT

CMD gunicorn --bind 0.0.0.0:$PORT --workers 1 main:app