from dotenv import load_dotenv
import os

load_dotenv()

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")
RABBITMQ_PORT = os.getenv("RABBITMQ_PORT")
RABBITMQ_QUEUE = os.getenv("RABBITMQ_QUEUE")
TIME_TO_DELAY_SEND_MESSAGE = os.getenv("TIME_TO_DELAY_SEND_MESSAGE")
