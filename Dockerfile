FROM python:3.8-slim as base

RUN apt-get update -qq
RUN apt-get install -y -qq python3-pip

COPY ./rasa_model_train/ /build/
COPY requirements.txt /build/
COPY runscript.sh /build/
COPY .env /build/

WORKDIR /build

RUN pip3 install -r requirements.txt

RUN python -m spacy download en_core_web_md

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# the entry point
EXPOSE 80
ENTRYPOINT ["/build/runscript.sh"]

#build command: docker build -t rasa_model .
#run command: docker run -p 80:80 -it rasa_model