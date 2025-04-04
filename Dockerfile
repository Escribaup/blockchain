FROM python:3.10

WORKDIR /app

COPY app/requirements.txt .
RUN pip install -r requirements.txt

COPY app/ .

EXPOSE 5000

CMD ["python", "blockchain_api.py"]
