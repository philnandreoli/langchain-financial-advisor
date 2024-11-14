FROM python:3.11-slim

RUN apt-get update && apt-get upgrade -y 

COPY ./requirements.txt ./

COPY ./src ./app

RUN pip install -r requirements.txt 

ARG CHAINLIT_PORT

EXPOSE ${CHAINLIT_PORT:-8000}

CMD chainlit run ./app/server.py --host 0.0.0.0 --port ${CHAINLIT_PORT:-8000} -h