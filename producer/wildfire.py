import time
from kafka import KafkaProducer
import requests
import pandas as pd
import io
import json
from datetime import datetime, timedelta

# === CONFIGURATION ===
KAFKA_BROKER = "localhost:9092"
KAFKA_TOPIC = "wildfires"
MAP_KEY = "369aa8b3849fa2f9f3e6210359d9bc4e"
PRODUCT = "VIIRS_NOAA21_NRT"
AREA = "world"
DAY = 1
MAX_MESSAGES = 50           # Max per cycle
FETCH_INTERVAL = 600        # 10 minutes (600 seconds)
SHORT_PAUSE = 10            # Pause after limit hit

# === Kafka Producer ===
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    key_serializer=lambda k: k.encode("utf-8"),
    linger_ms=100,
    batch_size=32768
)

# === Fetch Fire Alert Data ===
def fetch_fire_data():
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    url = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{MAP_KEY}/{PRODUCT}/{AREA}/{DAY}/{date_str}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        df = pd.read_csv(io.StringIO(response.text))

        # Combine acq_date + acq_time to datetime
        df["acq_datetime"] = pd.to_datetime(
            df["acq_date"] + " " + df["acq_time"].astype(str).str.zfill(4),
            format="%Y-%m-%d %H%M"
        )

        # Filter to last 2 hours
        now = datetime.utcnow()
        df = df[df["acq_datetime"] >= (now - timedelta(hours=2))]

        return df
    except Exception as e:
        print(f"[❌ Error fetching fire data] {e}")
        return pd.DataFrame()

# === Publish to Kafka ===
def publish_to_kafka(df: pd.DataFrame, already_sent: set):
    sent_count = 0

    for _, row in df.iterrows():
        if sent_count >= MAX_MESSAGES:
            print(f"[⛔ Limit Reached] Sent {MAX_MESSAGES} messages. Pausing...")
            time.sleep(SHORT_PAUSE)
            break

        event_id = f"{row.get('acq_date')}_{row.get('acq_time')}_{row.get('latitude')}_{row.get('longitude')}"

        if event_id in already_sent:
            continue
        already_sent.add(event_id)

        try:
            payload = {
                "latitude": row.get("latitude"),
                "longitude": row.get("longitude"),
                "brightness": row.get("bright_ti4") if "bright_ti4" in row else row.get("brightness"),
                "scan": row.get("scan"),
                "track": row.get("track"),
                "acq_date": row.get("acq_date"),
                "acq_time": row.get("acq_time"),
                "satellite": row.get("satellite"),
                "confidence": row.get("confidence"),
                "version": row.get("version"),
                "type": row.get("type"),
                "daynight": row.get("daynight"),
                "location": f"{row.get('latitude')},{row.get('longitude')}"
            }
            producer.send(KAFKA_TOPIC, key=event_id, value=payload)
            print(f"[+] Published fire alert at {payload['location']}")
            sent_count += 1
        except Exception as e:
            print(f"[⚠️ Kafka Error] {e}")

    producer.flush(timeout=10)

# === MAIN LOOP ===
if __name__ == "__main__":
    print("🔥 Starting Wildfire Kafka Producer (loop mode)...")
    already_sent_ids = set()

    try:
        while True:
            fire_df = fetch_fire_data()
            if not fire_df.empty:
                publish_to_kafka(fire_df, already_sent_ids)
            else:
                print("[ℹ️] No new fire alerts.")
            time.sleep(FETCH_INTERVAL)

    except KeyboardInterrupt:
        print("\n🛑 Stopping producer...")
    finally:
        producer.close(timeout=5)
