import json
import time
import psycopg2
from confluent_kafka import SerializingProducer

import tools.hiInterns as hiInterns
import tools.keejob as keejob
import tools.farojob as farojob
import tools.optionCarriere as optionCarriere

# connection = psycopg2.connect(
#     host="localhost",
#     database="job_board",
#     user="postgres",
#     password="postgres",
#     port="6543",
# )


def delivery_report(err, msg):
    if err is not None:
        print(f"Failed to deliver message: {err}")
    else:
        print(f"Message delivered to {msg.topic}: {msg.partition()}")


def hiInterns_old_links():
    # cursor = connection.cursor()
    # cursor.execute("SELECT link FROM hi_interns")
    # old_links = cursor.fetchall()
    # cursor.close()
    # return [link[0] for link in old_links]
    return []


def keejob_old_links():
    # cursor = connection.cursor()
    # cursor.execute("SELECT link FROM keejob")
    # old_links = cursor.fetchall()
    # cursor.close()
    # return [link[0] for link in old_links]
    return []


def farojob_old_links():
    # cursor = connection.cursor()
    # cursor.execute("SELECT link FROM farojob")
    # old_links = cursor.fetchall()
    # cursor.close()
    # return [link[0] for link in old_links]
    return []


def optionCarriere_old_links():
    # cursor = connection.cursor()
    # cursor.execute("SELECT link FROM option_carriere")
    # old_links = cursor.fetchall()
    # cursor.close()
    # return [link[0] for link in old_links]
    return []


def main():
    hiInters_latest_post = "None"
    keejob_latest_post = "None"
    farojob_latest_post = "None"
    optionCarriere_latest_post = "None"
    hiInterns_old_links_ = hiInterns_old_links()
    keejob_old_links_ = keejob_old_links()
    farojob_old_links_ = farojob_old_links()
    optionCarriere_old_links_ = optionCarriere_old_links()
    producer = SerializingProducer({"bootstrap.servers": "localhost:9092"})

    while True:
        hiInterns_post = hiInterns.get_latest_post()
        if hiInters_latest_post != hiInterns_post:
            hiInters_latest_post = hiInterns_post
            hiInterns_data, hiInterns_old_links_ = hiInterns.get_all_data(
                hiInterns_old_links_
            )
            for link, body in hiInterns_data.items():
                producer.produce(
                    "hi_interns",
                    key=link,
                    value=json.dumps({"link": link, "body": str(body)}),
                    on_delivery=delivery_report,
                )
                producer.poll(0)
                time.sleep(1)

        keejob_post = keejob.get_latest_post()
        if keejob_latest_post != keejob_post:
            keejob_latest_post = keejob_post
            keejob_data, keejob_old_links_ = keejob.get_all_data(keejob_old_links_)
            for link, body in keejob_data.items():
                producer.produce(
                    "keejob",
                    key=link,
                    value=json.dumps({"link": link, "body": str(body)}),
                    on_delivery=delivery_report,
                )
                producer.poll(0)
                time.sleep(1)

        farojob_post = farojob.get_latest_post()
        if farojob_latest_post != farojob_post:
            farojob_latest_post = farojob_post
            farojob_data, farojob_old_links_ = farojob.get_all_data(farojob_old_links_)
            for link, body in farojob_data.items():
                producer.produce(
                    "farojob",
                    key=link,
                    value=json.dumps(
                        {"link": link, "body": str(body[0]), "date": body[1]}
                    ),
                    on_delivery=delivery_report,
                )
                producer.poll(0)
                time.sleep(1)

        optionCarriere_post = optionCarriere.get_latest_post()
        if optionCarriere_latest_post != optionCarriere_post:
            optionCarriere_latest_post = optionCarriere_post
            optionCarriere_data, optionCarriere_old_links_ = (
                optionCarriere.get_all_data(optionCarriere_old_links_)
            )
            for link, body in optionCarriere_data.items():
                producer.produce(
                    "option_carriere",
                    key=link,
                    value=json.dumps({"link": link, "body": str(body)}),
                    on_delivery=delivery_report,
                )
                producer.poll(0)
                time.sleep(1)

        time.sleep(30)


if __name__ == "__main__":
    main()
