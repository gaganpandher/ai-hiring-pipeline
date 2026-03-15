import json
import asyncio
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from aiokafka.admin import AIOKafkaAdminClient, NewTopic
from app.core.config import settings
from loguru import logger
from typing import Any, Callable

_producer: AIOKafkaProducer | None = None


# ─── Topics ───────────────────────────────────────────────

TOPICS = [
    settings.KAFKA_TOPIC_APPLICATIONS,
    settings.KAFKA_TOPIC_SCORING_RESULTS,
    settings.KAFKA_TOPIC_BIAS_ALERTS,
    settings.KAFKA_TOPIC_AUDIT_LOG,
    settings.KAFKA_TOPIC_NOTIFICATIONS,
    settings.KAFKA_TOPIC_RECRUITER_ACTIONS,
]


async def create_topics():
    """Ensure all Kafka topics exist (idempotent)."""
    admin = AIOKafkaAdminClient(bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS)
    await admin.start()
    try:
        existing = await admin.list_topics()
        new_topics = [
            NewTopic(name=t, num_partitions=3, replication_factor=1)
            for t in TOPICS if t not in existing
        ]
        if new_topics:
            await admin.create_topics(new_topics)
            logger.info(f"✅ Created Kafka topics: {[t.name for t in new_topics]}")
        else:
            logger.info("✅ All Kafka topics already exist")
    except Exception as e:
        logger.warning(f"Topic creation warning (may already exist): {e}")
    finally:
        await admin.close()


# ─── Producer ─────────────────────────────────────────────

async def get_producer() -> AIOKafkaProducer:
    global _producer
    if _producer is None:
        _producer = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8") if k else None,
        )
        await _producer.start()
        logger.info("✅ Kafka producer started")
    return _producer


async def produce(topic: str, value: Any, key: str | None = None):
    """Publish a message to a Kafka topic."""
    producer = await get_producer()
    await producer.send_and_wait(topic, value=value, key=key)
    logger.debug(f"→ Kafka [{topic}] key={key}")


async def close_producer():
    global _producer
    if _producer:
        await _producer.stop()
        _producer = None
        logger.info("Kafka producer stopped")


# ─── Consumer factory ─────────────────────────────────────

async def consume(
    topics: list[str],
    group_id: str,
    handler: Callable[[str, Any], None],
):
    """
    Generic consumer loop.
    handler(topic, message_value) is called for every message.
    """
    consumer = AIOKafkaConsumer(
        *topics,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id=group_id,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        auto_offset_reset="earliest",
        enable_auto_commit=True,
    )
    await consumer.start()
    logger.info(f"✅ Kafka consumer [{group_id}] subscribed to {topics}")
    try:
        async for msg in consumer:
            try:
                await handler(msg.topic, msg.value)
            except Exception as e:
                logger.error(f"Consumer handler error on [{msg.topic}]: {e}")
    finally:
        await consumer.stop()


async def check_kafka_connection() -> bool:
    """Health-check: verify broker is reachable, with retries."""
    import asyncio
    for attempt in range(1, 6):
        try:
            admin = AIOKafkaAdminClient(bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS)
            await admin.start()
            await admin.list_topics()
            await admin.close()
            logger.info("✅ Kafka connection OK")
            return True
        except Exception as e:
            logger.warning(f"Kafka attempt {attempt}/5 failed: {e}")
            if attempt < 5:
                await asyncio.sleep(5)
    logger.error("❌ Kafka connection failed after 5 attempts")
    return False