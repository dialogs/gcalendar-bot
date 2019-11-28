FROM python:3.7
ENV LIBRARY_PATH=/lib:/usr/lib

WORKDIR "/app"
COPY . /app

RUN pip install -r requirements.txt


CMD ["python3", "src/main.py"]
