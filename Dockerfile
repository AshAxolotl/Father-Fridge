FROM python:latest

ADD requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

CMD ["python3", "-u", "/app/main.py"]
