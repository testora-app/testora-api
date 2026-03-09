FROM python:3.12.8-slim

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN adduser --disabled-password --no-create-home appuser
USER appuser

EXPOSE 8080

CMD ["gunicorn", "-w", "4", "-k", "gevent", "-b", "0.0.0.0:8080", "--timeout", "120", "run:app"]
