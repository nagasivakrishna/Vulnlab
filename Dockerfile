FROM python:3.11-alpine

WORKDIR /app

RUN python -m pip install Flask 

COPY . .

EXPOSE 5000

CMD ["python", "app.py"]