FROM python:3.8.10

WORKDIR /workspace

COPY requirements.txt .

RUN pip install --upgrade pip==21.1.1

RUN pip install -r requirements.txt

RUN mkdir -p /workspace/log

COPY . .