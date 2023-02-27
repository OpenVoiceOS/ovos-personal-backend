FROM ubuntu:latest

RUN apt-get update && \
  apt-get install -y git python3 python3-dev python3-pip curl build-essential libffi-dev python3-numpy rustc

RUN pip3 install SpeechRecognition==3.8.1

COPY . /tmp/ovos-backend
RUN pip3 install /tmp/ovos-backend

RUN pip3 install git+https://github.com/OpenVoiceOS/ovos-backend-manager

CMD ./tmp/ovos-backend/scripts/entrypoints.sh
