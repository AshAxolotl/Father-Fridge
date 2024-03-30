FROM python:latest

RUN pip install -r /app/requirements.txt

CMD ["python3", "/app/main.py"]
