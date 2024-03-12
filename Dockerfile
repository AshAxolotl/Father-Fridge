FROM python:latest

WORKDIR /usr/app/father-fridge-bot

COPY fridge .
RUN pip install -r requirements.txt

CMD ["python3", "./main.py"]
