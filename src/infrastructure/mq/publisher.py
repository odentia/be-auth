import json
import logging
import aio_pika
from aio_pika.abc import AbstractRobustConnection
from src.core.config import Settings, load_settings

logger = logging.getLogger(__name__)


class EventPublisher:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or load_settings()
        self.connection: AbstractRobustConnection = None
        self.channel: aio_pika.abc.AbstractChannel = None
        self.exchange: aio_pika.abc.AbstractExchange = None

    async def connect(self):
        try:
            self.connection = await aio_pika.connect_robust(self.settings.rabbitmq_url)
            self.channel = await self.connection.channel()

            self.exchange = await self.channel.declare_exchange(
                "blog_events",
                aio_pika.ExchangeType.TOPIC,
                durable=True
            )

            logger.info("Event publisher connected to RabbitMQ successfully")

        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    async def publish(self, event):
        if not self.exchange:
            logger.error("Event publisher not connected")
            return

        try:
            message_body = json.dumps(event.dict()).encode()
            message = aio_pika.Message(
                body=message_body,
                content_type="application/json",
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            )

            routing_key = f"auth.{event.event_type}"
            await self.exchange.publish(message, routing_key=routing_key)

            logger.debug(f"Event published: {event.event_type} -> {routing_key}")

        except Exception as e:
            logger.error(f"Failed to publish event: {e}")
            raise

    async def close(self):
        if self.connection:
            await self.connection.close()
            logger.info("Event publisher connection closed")
