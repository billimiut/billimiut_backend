FROM python:3.8.10

WORKDIR /workspace

COPY requirements.txt .

RUN pip install -r requirements.txt

RUN pip unintall pymongo bson

RUN pip install pymongo bson

RUN mkdir -p /workspace/log

COPY . .