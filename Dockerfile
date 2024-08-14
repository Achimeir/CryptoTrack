FROM python:3.11

RUN pip install -r requirements.txt

EXPOSE 80

WORKDIR /app

COPY app.py .

CMD ["fastapi", "run", ".\app\main.py"]