from kafka import KafkaProducer
import requests
import json
import time
from datetime import datetime, timezone

KAFKA_BROKER = "localhost:9092"
KAFKA_TOPIC = "earthquakes"
USGS_FEED_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson"

# Kafka producer setup
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    key_serializer=lambda k: k.encode("utf-8")
)

def fetch_earthquake_data():
    try:
        response = requests.get(USGS_FEED_URL)
        if response.status_code == 200:
            return response.json().get("features", [])
        else:
            print(f"[!] Failed to fetch data. Status code: {response.status_code}")
            return []
    except Exception as e:
        print(f"[ERROR] Failed to fetch earthquake data: {e}")
        return []

sent_event_ids = set()

def publish_to_kafka(events):
    new_events = 0
    for event in events:
        quake_id = event.get("id")
        if quake_id in sent_event_ids:
            continue  # Skip duplicates

        try:
            props = event["properties"]
            coords = event["geometry"]["coordinates"]

            payload = {
                "id": quake_id,
                "place": props.get("place"),
                "magnitude": props.get("mag"),
                "magType": props.get("magType"),
                "time": props.get("time"),
                "time_str": datetime.fromtimestamp(props.get("time", 0) / 1000, tz=timezone.utc).isoformat()
                            if props.get("time") else None,
                "longitude": coords[0],
                "latitude": coords[1],
                "depth": coords[2],
                "tsunami": str(props.get("tsunami")),  # Cast to string to match schema
                "sig": props.get("sig"),
                "type": props.get("type"),
                "status": props.get("status"),
                "gap": props.get("gap"),
                "rms": props.get("rms")
            }

            producer.send(KAFKA_TOPIC, key=quake_id, value=payload)
            sent_event_ids.add(quake_id)
            new_events += 1

            print(f"[+] Quake sent: {payload['place']} | Mag {payload['magnitude']}")
        except Exception as e:
            print(f"[ERROR processing event] {e}")

    if new_events == 0:
        print(f"[~] No new events found at {datetime.now().isoformat()}")

if __name__ == "__main__":
    print("🌐 Starting Earthquake Kafka Producer...")
    while True:
        quake_events = fetch_earthquake_data()
        if quake_events:
            publish_to_kafka(quake_events)
        else:
            print(f"[~] No data fetched at {datetime.now().isoformat()}")
        time.sleep(20)
