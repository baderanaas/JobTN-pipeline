import json
import time
from confluent_kafka import SerializingProducer

import tools.hiInterns as hiInterns
import tools.keejob as keejob
import tools.farojob as farojob
import tools.optionCarriere as optionCarriere


def delivery_report(err, msg):
    if err is not None:
        print(f"Failed to deliver message: {err}")
    else:
        print(f"Message delivered to {msg.topic()}: {msg.partition()}")


def main():
    hiInters_latest_post = "None"
    keejob_latest_post = "None"
    farojob_latest_post = "None"
    optionCarriere_latest_post = "None"

    producer = SerializingProducer({"bootstrap.servers": "localhost:9092"})

    while True:
        # hiInterns_post = hiInterns.get_latest_post()
        # if hiInters_latest_post != hiInterns_post:
        #     hiInters_latest_post = hiInterns_post
        #     hiInterns_data = hiInterns.get_all_data()

        #     for link, details in hiInterns_data.items():
        #         if not job_embeddings_collection.find_one(
        #             {"link": link, "expiration_date": {"$lt": six_months_ago}}
        #         ):
        #             producer.produce(
        #                 "hi_interns",
        #                 key=link,
        #                 value=json.dumps(details),
        #                 on_delivery=delivery_report,
        #             )

        #             producer.poll(0)
        #             time.sleep(1)

        keejob_post = keejob.get_latest_post()
        if keejob_latest_post != keejob_post:
            keejob_latest_post = keejob_post
            keejob_data = keejob.get_all_data()

            for link, details in keejob_data.items():
                producer.produce(
                    "keejob",
                    key=link,
                    value=json.dumps(details),
                    on_delivery=delivery_report,
                )

                producer.poll(0)
                time.sleep(1)

        farojob_post = farojob.get_latest_post()
        if farojob_latest_post != farojob_post:
            farojob_latest_post = farojob_post
            farojob_data = farojob.get_all_data()

            for link, details in farojob_data.items():
                producer.produce(
                    "farojob",
                    key=link,
                    value=json.dumps(details),
                    on_delivery=delivery_report,
                )

                producer.poll(0)
                time.sleep(1)

        optionCarriere_post = optionCarriere.get_latest_post()
        if optionCarriere_latest_post != optionCarriere_post:
            optionCarriere_latest_post = optionCarriere_post
            optionCarriere_data = optionCarriere.get_all_data()

            for link, details in optionCarriere_data.items():
                producer.produce(
                    "option_carriere",
                    key=link,
                    value=json.dumps(details),
                    on_delivery=delivery_report,
                )

                producer.poll(0)
                time.sleep(1)

        time.sleep(30)


if __name__ == "__main__":
    main()
