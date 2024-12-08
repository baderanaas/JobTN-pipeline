import json
import os
import logging
import threading
import time
from typing import Dict, List

from chonkie import TokenChunker
from tokenizers import Tokenizer
import polars as pl
from openai import OpenAI
from confluent_kafka import Consumer, KafkaError, KafkaException
from pymongo import MongoClient
from datetime import datetime

from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

load_dotenv()


class EmbeddingsProcessor:
    def __init__(
        self,
        kafka_config: Dict[str, str],
        mongodb_uri: str,
        topics: List[str],
        openai_api_key: str,
    ):

        # Set OpenAI API key
        self.openai_api_key = openai_api_key
        self.clientOpenAI = OpenAI(api_key=self.openai_api_key)

        # Kafka configuration
        self.conf = kafka_config
        self.topics = topics
        self.consumer = Consumer(self.conf)
        self.consumer.subscribe(self.topics)

        # MongoDB configuration
        self.mongodb_uri = mongodb_uri
        self.client = MongoClient(mongodb_uri)
        self.db = self.client["embeddings_db"]
        self.collection = self.db["job_embeddings"]

        # LazyFrames storage
        self.lazy_frames: Dict[str, pl.LazyFrame] = {
            topic: pl.LazyFrame([]) for topic in topics
        }

        # Threading event for controlled shutdown
        self.stop_event = threading.Event()
        self.tokenizer = Tokenizer.from_pretrained("gpt2")
        self.chunker = TokenChunker(self.tokenizer)

    def get_ada_embeddings(self, text: str) -> List[float]:

        try:
            response = (
                self.clientOpenAI.embeddings.create(
                    model="text-embedding-ada-002", input=[text]
                )
                .data[0]
                .embedding
            )
            return response
        except Exception as e:
            logger.error(f"Embeddings generation error: {e}")
            return []

    def preprocess_data(self, lazy_df: pl.LazyFrame) -> pl.LazyFrame:

        try:
            # Convert and handle expiration date
            lazy_df = lazy_df.with_columns(
                [
                    pl.col("expiration_date")
                    .cast(pl.Datetime)
                    .dt.cast_time_unit("ms")
                    .dt.strftime("%Y-%m-%d")
                    .fill_null(strategy="forward")
                    .alias("expiration_date")
                ]
            )

            # Filter out rows with missing critical information
            lazy_df = lazy_df.filter(
                (pl.col("company").is_not_null())
                & (pl.col("company") != "")
                & (pl.col("title").is_not_null())
                & (pl.col("title") != "")
                & (pl.col("description").is_not_null())
                & (pl.col("description") != "")
            )

            lazy_df = lazy_df.with_columns(
                pl.when(pl.col("expiration_date") == "0000-00-00")
                .then(None)
                .otherwise(pl.col("expiration_date"))
                .fill_null(strategy="forward")
                .alias("expiration_date")
            )

            # Create combined text for embeddings
            lazy_df = lazy_df.with_columns(
                [
                    (
                        pl.col("company")
                        + " "
                        + pl.col("title")
                        + " "
                        + pl.col("description")
                    ).alias("combined_text")
                ]
            )

            return lazy_df
        except Exception as e:
            logger.error(f"Data preprocessing error: {e}")
            return lazy_df

    def store_embeddings_in_mongo(self, df: pl.DataFrame):
        try:
            records = []
            for row in df.iter_rows(
                named=True
            ):  # Use named=True to get dictionary-like rows
                chunks = self.chunker(row["combined_text"])
                for chunk in chunks:
                    embedding = self.get_ada_embeddings(chunk.text)
                    record = {
                        "link": row["link"],
                        "company": row["company"],
                        "title": row["title"],
                        "workplace": row["workplace"],
                        "expiration_date": row["expiration_date"],
                        "embedding": embedding,
                        "description": row["description"],
                        "combined_text": row["combined_text"],
                    }
                    print("expiration date: ", record["expiration_date"])
                    records.append(record)

            if records:
                self.collection.insert_many(records)
                logger.info(f"Stored {len(records)} embeddings in MongoDB")
        except Exception as e:
            logger.error(f"MongoDB storage error: {e}")

    def process_kafka_messages(self):
        while not self.stop_event.is_set():
            try:
                msg = self.consumer.poll(timeout=1.0)

                if msg is None:
                    continue

                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        logger.info(
                            f"End of partition reached {msg.partition()}/{msg.offset()}"
                        )
                    else:
                        raise KafkaException(msg.error())
                else:
                    topic = msg.topic()
                    message_value = msg.value().decode("utf-8")
                    data = json.loads(message_value)
                    data_ = data["after"]

                    new_lazy_df = pl.LazyFrame([data_])
                    new_lazy_df = self.preprocess_data(new_lazy_df)

                    # Thread-safe update of lazy_frames
                    self.lazy_frames[topic] = new_lazy_df

            except Exception as e:
                logger.error(f"Kafka message processing error: {e}")
            finally:
                self.consumer.commit()

    def collect_lazy_frames(self):
        while not self.stop_event.is_set():
            try:
                if self.lazy_frames:
                    dataframes = pl.collect_all(
                        list(self.lazy_frames.values()),
                        type_coercion=True,
                        predicate_pushdown=True,
                        projection_pushdown=True,
                        slice_pushdown=True,
                        streaming=True,
                    )

                    for df in dataframes:
                        print(df.to_pandas().columns)
                        if not df.is_empty():
                            self.store_embeddings_in_mongo(df)

                time.sleep(5)  # Wait between collections
            except Exception as e:
                logger.error(f"LazyFrame collection error: {e}")

    def run(self):
        try:
            consumer_thread = threading.Thread(target=self.process_kafka_messages)
            collector_thread = threading.Thread(target=self.collect_lazy_frames)

            consumer_thread.start()
            collector_thread.start()

            # Wait for threads to complete (or be interrupted)
            consumer_thread.join()
            collector_thread.join()
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            self.stop_event.set()
        finally:
            self.consumer.close()


def main():
    # Load configurations from environment variables
    kafka_config = {
        "bootstrap.servers": "broker-debezium:9094",
        "group.id": "job-group",
        "auto.offset.reset": "earliest",
    }

    topics = "cdc.public.farojob,cdc.public.hi_interns,cdc.public.keejob,cdc.public.option_carriere".split(
        ","
    )
    mongodb_uri = "mongodb://host.docker.internal:27017/"
    openai_api_key = os.getenv("OPENAI_API_KEY")

    if not openai_api_key:
        logger.error("OpenAI API key is required!")
        return

    processor = EmbeddingsProcessor(kafka_config, mongodb_uri, topics, openai_api_key)
    processor.run()


if __name__ == "__main__":
    main()
