FROM python:3.12-slim

ENV TZ=Asia/Tehran

WORKDIR /app

COPY requirements.txt /app

RUN pip install -r requirements.txt

COPY app.py /app

EXPOSE 8000

CMD ["python", "app.py"]