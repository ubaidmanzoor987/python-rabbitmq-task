import json
import pika
import uuid
import time
import logging
from datetime import datetime

from config import (
    RABBITMQ_QUEUE,
    RABBITMQ_HOST,
    RABBITMQ_PORT,
    TIME_TO_DELAY_SEND_MESSAGE,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RabbitMQManager:
    def __init__(self, host, port, queue):
        self.host = host
        self.port = port
        self.queue = queue
        self.connection = None
        self.channel = None

    def connect(self):
        attempts = 5
        delay = 5
        for attempt in range(1, attempts + 1):
            try:
                self.connection = pika.BlockingConnection(
                    pika.ConnectionParameters(host=self.host, port=int(self.port))
                )
                self.channel = self.connection.channel()
                self.channel.queue_declare(queue=self.queue, durable=True)
                logger.info("Connected to RabbitMQ successfully")
                return True
            except pika.exceptions.AMQPConnectionError as e:
                logger.warning(f"Connection attempt {attempt}/{attempts} failed: {e}")
                time.sleep(delay)
        logger.error("Failed to connect to RabbitMQ after several attempts")
        return False

    def publish_message(self):
        message = {
            "message_id": str(uuid.uuid4()),
            "created_on": datetime.now().isoformat(),
        }
        logger.info("Message before send: %s", message)
        try:
            self.channel.basic_publish(
                exchange="",
                routing_key=self.queue,
                body=json.dumps(message),
                properties=pika.BasicProperties(delivery_mode=2),
            )
            logger.info("Message sent successfully")
        except (pika.exceptions.AMQPError, IOError) as e:
            logger.error(f"Failed to publish message: {e}")

    def close_connection(self):
        if self.connection and self.connection.is_open:
            self.connection.close()
            logger.info("RabbitMQ connection closed")

    def run(self):

        if not self.connect():
            return
        try:
            while True:
                self.publish_message()
                time.sleep(int(TIME_TO_DELAY_SEND_MESSAGE))
        except KeyboardInterrupt:
            logger.info("Process interrupted by user")
        finally:
            self.close_connection()


if __name__ == "__main__":
    rabbitmq_manager = RabbitMQManager(RABBITMQ_HOST, RABBITMQ_PORT, RABBITMQ_QUEUE)
    rabbitmq_manager.run()
