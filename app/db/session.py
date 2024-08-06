from pymongo.mongo_client import MongoClient
import certifi

from dotenv import load_dotenv,find_dotenv
import os

load_dotenv(find_dotenv())

username = os.getenv('MONGO_USER')
password = os.getenv('MONGO_PASS')
host = os.getenv('MONGO_HOST')
query_param = 'ssl=false'
port = os.getenv('MONGO_PORT')
ca = certifi.where()
uri = f"mongodb://{username}:{password}@{host}:{port}/?{query_param}"

dbname = 'billimiut'
client = MongoClient(uri)[dbname]
client.command('ping')