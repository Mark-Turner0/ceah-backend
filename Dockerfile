# syntax=docker/dockerfile:experimental

FROM python:latest

WORKDIR /ceah-backend

COPY ./ .

RUN python3 -m pip install pymongo

RUN python3 -m pip install dnspython

RUN --mount=type=secret,id=DB_USERNAME --mount=type=secret,id=DB_PASSWORD python3 -u update.py $(cat /run/secrets/DB_USERNAME) $(cat /run/secrets/DB_PASSWORD)

CMD python3 -u main.py $DB_USERNAME $DB_PASSWORD
