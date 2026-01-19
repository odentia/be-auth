from contextlib import asynccontextmanager
from typing import AsyncIterator
import asyncio

from fastapi import FastAPI

from src.core.config import Settings
from src.core.db import init_engine, close_engine, init_session_factory
from src.core.logging import get_logger
from src.infrastructure.mq.publisher import EventPublisher
from src.infrastructure.mq.consumer import EventConsumer

log = get_logger(__name__)


async def start_consumer(consumer: EventConsumer):
    """Запуск consumer в фоновой задаче"""
    try:
        await consumer.start_consuming()
    except Exception as e:
        log.error(f"Consumer error: {e}")


def build_lifespan(settings: Settings):

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        # --- Startup ---
        log.info("Starting service...", extra={"app": settings.app_name, "env": settings.env})

        # DB engine & session factory
        engine = await init_engine(settings.database_url, echo=settings.sql_echo)
        sf = init_session_factory(engine)
        init_session_factory(engine)
        app.state.engine = engine
        app.state.session_factory = sf
        app.state.ready = True

        # RabbitMQ Publisher
        event_publisher = None
        try:
            event_publisher = EventPublisher(settings)
            await event_publisher.connect()
            app.state.event_publisher = event_publisher
            log.info("RabbitMQ publisher connected")
        except Exception as e:
            log.warning(f"Failed to connect RabbitMQ publisher: {e}. Events will not be published.")
            app.state.event_publisher = None

        # RabbitMQ Consumer (опционально, если нужно слушать события)
        event_consumer = None
        consumer_task = None
        try:
            event_consumer = EventConsumer(settings)
            await event_consumer.connect()
            
            # Регистрируем обработчики событий (пример)
            # event_consumer.register_handler("user_deleted", handle_user_deleted)
            
            # Запускаем consumer в фоновой задаче
            consumer_task = asyncio.create_task(start_consumer(event_consumer))
            app.state.event_consumer = event_consumer
            log.info("RabbitMQ consumer started")
        except Exception as e:
            log.warning(f"Failed to start RabbitMQ consumer: {e}. Events will not be consumed.")
            app.state.event_consumer = None

        log.info("Service is up")

        try:
            yield
        finally:
            # --- Shutdown ---
            log.info("Shutting down service...")
            app.state.ready = False

            # Останавливаем consumer
            if consumer_task:
                consumer_task.cancel()
                try:
                    await consumer_task
                except asyncio.CancelledError:
                    pass

            if event_consumer:
                try:
                    await event_consumer.close()
                except Exception as e:
                    log.error(f"Error closing consumer: {e}")

            # Закрываем publisher
            if event_publisher:
                try:
                    await event_publisher.close()
                except Exception as e:
                    log.error(f"Error closing publisher: {e}")

            # Close DB engine
            await close_engine(engine)

            log.info("Bye")

    return lifespan
