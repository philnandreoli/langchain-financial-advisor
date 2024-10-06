FROM python:3.12-slim

RUN apt-get update && apt-get upgrade -y 

COPY ./requirements.txt ./

COPY ./src ./app

RUN pip install -r requirements.txt 

ARG CHAT_PORT

EXPOSE ${CHAT_PORT:-8501}

CMD streamlit run ./app/server.py --server.port ${CHAT_PORT:-8501}

#ENTRYPOINT ["streamlit", "run", "./app/server.py", "--server.port ${PORT:-8501}"]