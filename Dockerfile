FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /simple-search-ui

RUN apt-get update && apt-get install -y git && pip install pipenv

COPY Pipfile Pipfile.lock /simple-search-ui/

RUN pipenv install --deploy --ignore-pipfile

COPY . /simple-search-ui/

EXPOSE 8000

