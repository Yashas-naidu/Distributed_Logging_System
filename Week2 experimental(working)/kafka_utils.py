from kafka import KafkaProducer, KafkaConsumer
import json
from datetime import datetime
import threading
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(_name_)

class KafkaWrapper:
    def _init_(self, bootstrap_servers='localhost:9092'):
        self.bootstrap_servers = bootstrap_servers
        self.producer = None
        self.consumer = None
        self._setup_producer()

    def _setup_producer(self):
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=[self.bootstrap_servers],
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            logger.info("Kafka producer initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Kafka producer: {e}")
            raise

    def send_message(self, topic: str, message: dict):
        try:
            future = self.producer.send(topic, value=message)
            future.get(timeout=10)  # Wait for message to be sent
            logger.info(f"Message sent to topic {topic}: {message}")
        except Exception as e:
            logger.error(f"Failed to send message to Kafka: {e}")
            raise

    def start_consumer(self, topic: str, message_handler, group_id=None):
        def consume():
            try:
                self.consumer = KafkaConsumer(
                    topic,
                    bootstrap_servers=[self.bootstrap_servers],
                    group_id=group_id or f'group-{datetime.now().timestamp()}',
                    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                    auto_offset_reset='latest'
                )
                
                logger.info(f"Started consuming from topic: {topic}")
                for message in self.consumer:
                    try:
                        message_handler(message.value)
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
                        
            except Exception as e:
                logger.error(f"Consumer error: {e}")
                raise
                
        # Start consumer in a separate thread
        consumer_thread = threading.Thread(target=consume, daemon=True)
        consumer_thread.start()
        return consumer_thread

    def close(self):
        if self.producer:
            self.producer.close()
        if self.consumer:
            self.consumer.close()