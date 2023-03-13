FROM python:3

WORKDIR /tgbot

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY ./tgbot .