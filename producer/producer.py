from kafka import KafkaProducer
import requests
import json
import time

KAFKA_BROKER = "localhost:9092"
KAFKA_TOPIC = "earthquakes"
USGS_FEED_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson"

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)


def fetch_earthquake_data():
    try:
        response = requests.get(USGS_FEED_URL)
        data = response.json()
        return data["features"]
    except Exception as e:
        print(f"ERROR : {e}")

sent_event_ids = set()

def publish_to_kafka(events):
    for event in events:
        if event["id"] in sent_event_ids:
            continue  # skip duplicate
        quake = {
            "id": event["id"],
            "place": event["properties"]["place"],
            "magnitude": event["properties"]["mag"],
            "time": event["properties"]["time"],
            "longitude": event["geometry"]["coordinates"][0],
            "latitude": event["geometry"]["coordinates"][1],
            "depth": event["geometry"]["coordinates"][2],
        }
        print(f"[+] New quake: {quake['place']} | Mag {quake['magnitude']}")
        producer.send(KAFKA_TOPIC, value=quake)
        sent_event_ids.add(event["id"])



if __name__ == "__main__":
    print("🌐 Starting Earthquake Kafka Producer...")
    while True:
        events = fetch_earthquake_data()
        if events:
            publish_to_kafka(events)
        time.sleep(60)  # fetch every 1 min
