FROM python:latest

WORKDIR /ceah-backend

COPY ./ .

RUN python3 -m pip install pymongo

RUN python3 -m pip install dnspython

RUN python3 -m pip install feedparser

CMD sh startup.sh
