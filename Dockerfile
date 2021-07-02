FROM python:latest

WORKDIR /ceah-backend

COPY ./ .

RUN python3 update.py

RUN mkdir data

CMD ["python3", "-u", "main.py"]
