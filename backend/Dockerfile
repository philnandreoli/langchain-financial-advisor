FROM python:3.11-slim

RUN apt-get update && apt-get upgrade -y 

COPY ./requirements.txt ./

COPY ./src ./app

RUN pip install -r requirements.txt 

ARG PORT

EXPOSE ${PORT:-8000}

CMD exec uvicorn app.graph_server:app --host 0.0.0.0 --port ${PORT:-8000}