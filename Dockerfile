FROM python:3.8.10

WORKDIR /workspace

COPY requirements.txt .

RUN apt-get update && \
    apt-get install -y \

RUN pip install -r requirements.txt

RUN mkdir -p /workspace/log

COPY . .