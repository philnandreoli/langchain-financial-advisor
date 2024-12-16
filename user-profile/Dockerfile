FROM python:3.11-slim

RUN apt-get update && apt-get upgrade -y

COPY .requirements.txt ./

COPY ./src ./app

RUN pip install -r requirements.txt

ARG PORT

EXPOSE ${PORT:-7500}

CMD exec uvicorn app.server:app --host 0.0.0.0 --port ${PORT:-7500}