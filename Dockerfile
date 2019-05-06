FROM python:3.7-alpine
ENV LIBRARY_PATH=/lib:/usr/lib
ENV BOT_ENDPOINT=$BOT_ENDPOINT
ENV BOT_TOKEN=$BOT_TOKEN

WORKDIR "/tmp"
COPY . /tmp

RUN apk add build-base python3-dev py3-pip jpeg-dev zlib-dev libffi-dev libressl-dev
RUN apk add --no-cache py-cryptography
RUN python3 -m pip install -r requirements.txt


CMD ["python3", "src/main.py"]
