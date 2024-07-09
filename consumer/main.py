import socket
import pika
import time
import logging
import json
from config import RABBITMQ_PORT, RABBITMQ_QUEUE, RABBITMQ_HOST

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Consumer")


class RabbitMQConsumer:
    def __init__(self, host, port, queue):
        self.host = host
        self.port = port
        self.queue = queue
        self.connection = None
        self.channel = None

    def connect(self, retries=5, delay=5):
        for attempt in range(1, retries + 1):
            try:
                parameters = pika.ConnectionParameters(host=self.host, port=self.port)
                self.connection = pika.BlockingConnection(parameters)
                logger.info("Successfully connected to RabbitMQ")
                return
            except pika.exceptions.AMQPConnectionError as e:
                logger.warning(f"Connection attempt {attempt}/{retries} failed: {e}")
                time.sleep(delay)
        raise Exception("Failed to connect to RabbitMQ after several attempts")

    def setup_channel(self):
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=self.queue, durable=True)
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(
            queue=self.queue, on_message_callback=self.message_callback
        )

    def message_callback(self, ch, method, properties, body):
        try:
            message_data = json.loads(body)
            logger.info("Processed message: %s", message_data)
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding message body: {e}")
        finally:
            ch.basic_ack(delivery_tag=method.delivery_tag)

    def start_consuming(self):
        while True:
            try:
                self.connect()
                self.setup_channel()

                logger.info("Waiting for messages. Press CTRL+C to exit.")
                self.channel.start_consuming()
            except (
                pika.exceptions.AMQPConnectionError,
                pika.exceptions.StreamLostError,
                socket.gaierror,
            ) as e:
                logger.error(f"Connection lost: {e}")
                time.sleep(5)  # Wait before attempting to reconnect
            except Exception as e:
                logger.error(f"Error in start_consuming: {e}")
                break  # Exit on unexpected exceptions
            finally:
                self.close_connection()

    def close_connection(self):
        if self.connection and self.connection.is_open:
            self.connection.close()
            logger.info("RabbitMQ connection closed")


if __name__ == "__main__":
    consumer = RabbitMQConsumer(RABBITMQ_HOST, RABBITMQ_PORT, RABBITMQ_QUEUE)
    consumer.start_consuming()
